"""Client-scoped opaque credentials, independent of any product models."""

# Django Imports
from django.conf import settings
from django.db import models


class MobileGrant(models.Model):
    """A short-lived, single-use authorization code bound to S256 PKCE."""

    client_id = models.CharField(max_length=128, db_index=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, db_constraint=False
    )
    digest = models.CharField(max_length=64, unique=True)
    challenge = models.CharField(max_length=43)
    redirect_uri = models.CharField(max_length=200)
    auth_hash = models.CharField(max_length=64)
    expires_at = models.DateTimeField()
    consumed = models.BooleanField(default=False)


class MobileSession(models.Model):
    """One device session; only digests of bearer credentials reach the DB."""

    client_id = models.CharField(max_length=128, db_index=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, db_constraint=False
    )
    access_digest = models.CharField(max_length=64, unique=True)
    refresh_digest = models.CharField(max_length=64, unique=True)
    auth_hash = models.CharField(max_length=64)
    access_expires_at = models.DateTimeField()
    expires_at = models.DateTimeField()
    revoked = models.BooleanField(default=False)
