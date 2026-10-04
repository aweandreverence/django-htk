"""Explicit per-product configuration; no trusted client data from requests."""

# Python Standard Library Imports
import re
from dataclasses import dataclass
from urllib.parse import urlsplit

# Django Imports
from django.core.exceptions import ImproperlyConfigured


@dataclass(frozen=True)
class NativeClient:
    client_id: str
    redirect_uri: str
    app_name: str
    login_url_name: str
    consent_description: str = "your account data"
    access_seconds: int = 900
    grant_seconds: int = 120
    session_seconds: int = 30 * 86400

    def __post_init__(self) -> None:
        """Reject unsafe callbacks/configuration before a credential can be issued."""
        if not isinstance(self.client_id, str) or not re.fullmatch(
            r"[A-Za-z0-9._:-]{1,128}", self.client_id
        ):
            raise ImproperlyConfigured(
                "Native client requires a stable client_id."
            )
        try:
            target = urlsplit(self.redirect_uri)
            valid = (
                bool(target.scheme)
                and bool(target.netloc)
                and target.scheme not in ("http", "javascript", "data", "file")
                and not target.query
                and not target.fragment
                and not target.username
                and not target.password
                and not any(c.isspace() for c in self.redirect_uri)
            )
        except (TypeError, ValueError):
            valid = False
        if not valid or len(self.redirect_uri) > 200:
            raise ImproperlyConfigured(
                "Native client requires an exact HTTPS or private-scheme callback."
            )
        if not all(
            isinstance(v, str) and v.strip()
            for v in (
                self.app_name,
                self.login_url_name,
                self.consent_description,
            )
        ):
            raise ImproperlyConfigured(
                "Native client requires app, login route and consent labels."
            )
        if any(
            type(v) is not int or v <= 0
            for v in (
                self.access_seconds,
                self.grant_seconds,
                self.session_seconds,
            )
        ):
            raise ImproperlyConfigured(
                "Native credential lifetimes must be positive seconds."
            )
