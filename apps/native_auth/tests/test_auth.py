"""Real ORM/HTTP contract and cross-client isolation, independent of A&R."""

# Python Standard Library Imports
from dataclasses import replace
from datetime import timedelta
from urllib.parse import (
    parse_qs,
    urlencode,
    urlsplit,
)

# Django Imports
from django.contrib.auth import get_user_model
from django.core.exceptions import ImproperlyConfigured
from django.test import (
    Client,
    TestCase,
)
from django.utils import timezone

# HTK Imports
from htk.apps.native_auth.models import (
    MobileGrant,
    MobileSession,
)
from htk.apps.native_auth.services import (
    NativeAuthService,
    challenge,
)
from htk.apps.native_auth.tests.urls import (
    client,
    service,
)


class NativeAuthTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            "reader", password="test"
        )
        self.alpha, self.beta = service(), service("beta")
        self.verifier = "v" * 43

    def grant(self):
        return self.alpha.issue_grant(self.user, challenge(self.verifier))

    def test_rfc_pkce_and_invalid_configuration(self):
        self.assertEqual(
            challenge("dBjftJeZ4CVP-mB92K27uhbUJU1p1r_wW1gFWFOEjXk"),
            "E9Melhoa2OwvFrEMTJguCHaoeK1t8URWbuGJSstw-cM",
        )
        for uri in [
            "http://example.test/callback",
            "alpha://auth/callback?redirect=bad",
            "alpha://auth/callback#x",
            "javascript:alert(1)",
            "alpha://user:pass@auth/callback",
        ]:
            with self.assertRaises(ImproperlyConfigured):
                replace(client(), redirect_uri=uri)
        with self.assertRaises(ImproperlyConfigured):
            replace(client(), client_id="")

    def test_clients_cannot_consume_authenticate_refresh_or_revoke_each_other(
        self,
    ):
        code = self.grant()
        self.assertIsNone(self.beta.exchange(code, self.verifier))
        moved = NativeAuthService(
            replace(client(), redirect_uri="alpha://new/callback")
        )
        self.assertIsNone(moved.exchange(code, self.verifier))
        tokens = self.alpha.exchange(code, self.verifier)
        self.assertIsNotNone(tokens)
        self.assertIsNone(
            self.beta.authenticate("Bearer " + tokens["access_token"])
        )
        self.assertIsNone(self.beta.refresh(tokens["refresh_token"]))
        self.beta.revoke(tokens["refresh_token"])
        self.assertEqual(
            self.alpha.authenticate("Bearer " + tokens["access_token"]),
            self.user,
        )
        rotated = self.alpha.refresh(tokens["refresh_token"])
        self.assertIsNotNone(rotated)
        self.assertIsNone(self.alpha.refresh(tokens["refresh_token"]))
        self.assertIsNone(
            self.alpha.authenticate("Bearer " + tokens["access_token"])
        )
        self.alpha.revoke(rotated["refresh_token"])
        self.assertIsNone(
            self.alpha.authenticate("Bearer " + rotated["access_token"])
        )

    def test_wrong_verifier_replay_and_expiry(self):
        code = self.grant()
        self.assertIsNone(self.alpha.exchange(code, "x" * 43))
        self.assertIsNotNone(self.alpha.exchange(code, self.verifier))
        self.assertIsNone(self.alpha.exchange(code, self.verifier))
        code = self.grant()
        MobileGrant.objects.update(
            expires_at=timezone.now() - timedelta(seconds=1)
        )
        self.assertIsNone(self.alpha.exchange(code, self.verifier))

    def test_session_lifetime_and_password_change(self):
        tokens = self.alpha.exchange(self.grant(), self.verifier)
        expiry = MobileSession.objects.get().expires_at
        tokens = self.alpha.refresh(tokens["refresh_token"])
        self.assertEqual(MobileSession.objects.get().expires_at, expiry)
        self.user.set_password("changed")
        self.user.save()
        self.assertIsNone(
            self.alpha.authenticate("Bearer " + tokens["access_token"])
        )
        self.assertIsNone(self.alpha.refresh(tokens["refresh_token"]))
        tokens = self.alpha.exchange(self.grant(), self.verifier)
        MobileSession.objects.update(
            expires_at=timezone.now() - timedelta(seconds=1)
        )
        self.assertIsNone(self.alpha.refresh(tokens["refresh_token"]))

    def test_consent_csrf_and_http_exchange_contract(self):
        browser = Client(enforce_csrf_checks=True)
        params = {
            "client_id": "alpha",
            "redirect_uri": client().redirect_uri,
            "code_challenge_method": "S256",
            "code_challenge": challenge(self.verifier),
            "state": "s" * 43,
        }
        url = "/alpha/authorize?" + urlencode(params)
        self.assertEqual(browser.get(url).status_code, 302)
        browser.force_login(self.user)
        response = browser.get(url)
        self.assertContains(response, "Connect Alpha")
        self.assertEqual(response["Referrer-Policy"], "same-origin")
        self.assertEqual(browser.post(url, {"approve": "yes"}).status_code, 403)
        consent = {
            "approve": "yes",
            "csrfmiddlewaretoken": browser.cookies["csrftoken"].value,
        }
        # Exercise real HTTPS origin checks, not the test client's default HTTP
        # request with no Origin/Referer. Never trust null or unrelated origins.
        for origin in ("null", "https://untrusted.example"):
            self.assertEqual(
                browser.post(
                    url, consent, secure=True, HTTP_ORIGIN=origin
                ).status_code,
                403,
            )
        self.assertFalse(MobileGrant.objects.exists())
        cancelled = browser.post(
            url,
            {**consent, "approve": "no"},
            secure=True,
            HTTP_ORIGIN="https://testserver",
        )
        self.assertEqual(cancelled.status_code, 302)
        self.assertEqual(cancelled["Referrer-Policy"], "no-referrer")
        self.assertEqual(
            parse_qs(urlsplit(cancelled["Location"]).query),
            {"state": [params["state"]], "error": ["access_denied"]},
        )
        self.assertFalse(MobileGrant.objects.exists())
        result = browser.post(
            url, consent, secure=True, HTTP_ORIGIN="https://testserver"
        )
        self.assertEqual(result.status_code, 302)
        self.assertEqual(result["Referrer-Policy"], "no-referrer")
        code = parse_qs(urlsplit(result["Location"]).query)["code"][0]
        payload = {
            "client_id": "alpha",
            "grant_type": "authorization_code",
            "redirect_uri": client().redirect_uri,
            "code": code,
            "code_verifier": self.verifier,
        }
        self.assertEqual(
            browser.post(
                "/beta/token", payload, content_type="application/json"
            ).status_code,
            400,
        )
        response = browser.post(
            "/alpha/token", payload, content_type="application/json"
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["expires_in"], 900)
        self.assertEqual(response["Cache-Control"], "no-store")
        self.assertEqual(browser.get(url + "&client_id=beta").status_code, 400)
        params["redirect_uri"] = "beta://auth/callback"
        self.assertEqual(
            browser.get("/alpha/authorize", params).status_code, 400
        )

    def test_disabled_and_deleted_accounts_fail_closed(self):
        code = self.grant()
        tokens = self.alpha.exchange(code, self.verifier)
        self.user.is_active = False
        self.user.save()
        self.assertIsNone(
            self.alpha.authenticate("Bearer " + tokens["access_token"])
        )
        self.assertIsNone(self.alpha.refresh(tokens["refresh_token"]))
        MobileSession.objects.update(user_id=987654321)
        self.assertIsNone(
            self.alpha.authenticate("Bearer " + tokens["access_token"])
        )
