"""Reusable PKCE exchange and client-scoped opaque device sessions."""

# Python Standard Library Imports
import base64
import hashlib
import re
import secrets
from datetime import timedelta
from typing import Any

# Django Imports
from django.contrib.auth.models import AbstractBaseUser
from django.core.exceptions import (
    ImproperlyConfigured,
    ObjectDoesNotExist,
)
from django.db import (
    router,
    transaction,
)
from django.utils import timezone
from django.utils.crypto import constant_time_compare

from .config import NativeClient
from .models import (
    MobileGrant,
    MobileSession,
)

VERIFIER_RE = re.compile(r"^[A-Za-z0-9._~-]{43,128}$")
CHALLENGE_RE = re.compile(r"^[A-Za-z0-9_-]{43}$")


def digest(value: str) -> str:
    """Hash high-entropy opaque credentials; never log their raw values."""
    return hashlib.sha256(value.encode("ascii")).hexdigest()


def challenge(verifier: str) -> str:
    """RFC 7636 S256, unpadded URL-safe base64."""
    return (
        base64.urlsafe_b64encode(
            hashlib.sha256(verifier.encode("ascii")).digest()
        )
        .decode()
        .rstrip("=")
    )


def current_user(row: MobileGrant | MobileSession) -> AbstractBaseUser | None:
    """Disablement, password reset or removed Accounts records invalidate access."""
    try:
        user = row.user
    except ObjectDoesNotExist:
        return None
    return (
        user
        if user.is_active
        and constant_time_compare(row.auth_hash, user.get_session_auth_hash())
        else None
    )


class NativeAuthService:
    """Bind all credential operations to one trusted server-side client config."""

    def __init__(self, client: NativeClient) -> None:
        self.client = client
        self.database = router.db_for_write(MobileSession)
        if router.db_for_write(MobileGrant) != self.database:
            raise ImproperlyConfigured(
                "Native grants and sessions require the same transaction database."
            )

    def grants(self) -> Any:
        """Use the write connection even for reads so replica lag cannot revive access."""
        return MobileGrant.objects.using(self.database).filter(
            client_id=self.client.client_id
        )

    def sessions(self) -> Any:
        """No credential operation may escape the bound client audience."""
        return MobileSession.objects.using(self.database).filter(
            client_id=self.client.client_id
        )

    def issue_grant(self, user: AbstractBaseUser, code_challenge: str) -> str:
        """Call only after browser consent; reject inactive users and malformed PKCE."""
        if not user.is_active or not CHALLENGE_RE.fullmatch(code_challenge):
            raise ValueError("Invalid native authorization request.")
        code = secrets.token_urlsafe(32)
        self.grants().create(
            client_id=self.client.client_id,
            user=user,
            digest=digest(code),
            challenge=code_challenge,
            redirect_uri=self.client.redirect_uri,
            auth_hash=user.get_session_auth_hash(),
            expires_at=timezone.now()
            + timedelta(seconds=self.client.grant_seconds),
        )
        return code

    def credentials(self) -> tuple[str, str, dict]:
        """Generate a replacement pair, never persistent raw secrets."""
        access, refresh = secrets.token_urlsafe(32), secrets.token_urlsafe(32)
        return (
            access,
            refresh,
            {
                "access_token": access,
                "refresh_token": refresh,
                "token_type": "Bearer",
                "expires_in": self.client.access_seconds,
            },
        )

    def exchange(self, code: str, verifier: str) -> dict | None:
        """Consume a grant once; wrong client, redirect or verifier cannot burn it."""
        if not CHALLENGE_RE.fullmatch(code) or not VERIFIER_RE.fullmatch(
            verifier
        ):
            return None
        with transaction.atomic(using=self.database):
            grant = (
                self.grants()
                .filter(
                    digest=digest(code),
                    consumed=False,
                    redirect_uri=self.client.redirect_uri,
                    expires_at__gt=timezone.now(),
                )
                .first()
            )
            user = current_user(grant) if grant else None
            if user is None or not constant_time_compare(
                grant.challenge, challenge(verifier)
            ):
                return None
            if (
                not self.grants()
                .filter(pk=grant.pk, consumed=False)
                .update(consumed=True)
            ):
                return None
            access, refresh, payload = self.credentials()
            self.sessions().create(
                client_id=self.client.client_id,
                user=user,
                auth_hash=grant.auth_hash,
                access_digest=digest(access),
                refresh_digest=digest(refresh),
                access_expires_at=timezone.now()
                + timedelta(seconds=self.client.access_seconds),
                expires_at=timezone.now()
                + timedelta(seconds=self.client.session_seconds),
            )
            return payload

    def refresh(self, token: str) -> dict | None:
        """Rotate atomically, without extending absolute session lifetime."""
        if not CHALLENGE_RE.fullmatch(token):
            return None
        with transaction.atomic(using=self.database):
            row = (
                self.sessions()
                .filter(
                    refresh_digest=digest(token),
                    revoked=False,
                    expires_at__gt=timezone.now(),
                )
                .first()
            )
            if row is None or current_user(row) is None:
                return None
            access, replacement, payload = self.credentials()
            changed = (
                self.sessions()
                .filter(pk=row.pk, refresh_digest=digest(token), revoked=False)
                .update(
                    access_digest=digest(access),
                    refresh_digest=digest(replacement),
                    access_expires_at=timezone.now()
                    + timedelta(seconds=self.client.access_seconds),
                )
            )
            return payload if changed else None

    def authenticate(self, header: str) -> AbstractBaseUser | None:
        """Only this client's valid bearer header authenticates its business APIs."""
        if not header.startswith("Bearer ") or not CHALLENGE_RE.fullmatch(
            header[7:]
        ):
            return None
        row = (
            self.sessions()
            .filter(
                access_digest=digest(header[7:]),
                revoked=False,
                access_expires_at__gt=timezone.now(),
                expires_at__gt=timezone.now(),
            )
            .first()
        )
        return current_user(row) if row else None

    def revoke(self, token: str) -> None:
        """Idempotent device logout; cannot revoke a different client's session."""
        if CHALLENGE_RE.fullmatch(token):
            self.sessions().filter(refresh_digest=digest(token)).update(
                revoked=True
            )
