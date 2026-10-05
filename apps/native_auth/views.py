"""Composable native account HTTP boundary; products supply consent/configuration."""

# Python Standard Library Imports
from types import SimpleNamespace
from typing import Callable
from urllib.parse import urlencode

# Django Imports
from django.http import (
    HttpRequest,
    HttpResponse,
    JsonResponse,
)
from django.middleware.csrf import get_token
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.html import format_html
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import (
    csrf_exempt,
    csrf_protect,
)
from django.views.decorators.http import require_http_methods

# HTK Imports
from htk.api.http import (
    parse_string_json_body as body,
    private_json_response as json_reply,
)
from htk.apps.native_auth import services as auth
from htk.apps.native_auth.services import NativeAuthService


def build_views(factory: Callable[[], NativeAuthService]) -> SimpleNamespace:
    """Build independent endpoints without global client state or product imports."""

    @never_cache
    @csrf_protect
    @require_http_methods(["GET", "POST"])
    def authorize(request: HttpRequest) -> HttpResponse:
        """Use the established web account session, then ask for device consent."""
        service = factory()
        client = service.client
        query = request.GET
        valid = (
            all(
                len(query.getlist(k)) == 1
                for k in (
                    "client_id",
                    "redirect_uri",
                    "code_challenge_method",
                    "code_challenge",
                    "state",
                )
            )
            and query.get("client_id") == client.client_id
            and query.get("redirect_uri") == client.redirect_uri
            and query.get("code_challenge_method") == "S256"
            and auth.CHALLENGE_RE.fullmatch(query.get("code_challenge", ""))
            and auth.CHALLENGE_RE.fullmatch(query.get("state", ""))
        )
        if not valid:
            response = json_reply({"error": "invalid_request"}, 400)
        elif not request.user.is_authenticated or not request.user.is_active:
            response = redirect(
                reverse(client.login_url_name)
                + "?"
                + urlencode({"next": request.get_full_path()})
            )
        elif request.method == "POST":
            params = {"state": query["state"]}
            if request.POST.get("approve") == "yes":
                params["code"] = service.issue_grant(
                    request.user, query["code_challenge"]
                )
            else:
                params["error"] = "access_denied"
            # HttpResponseRedirect disallows custom schemes; the URI here is fixed,
            # never supplied by the requester.
            response = HttpResponse(status=302)
            response["Location"] = client.redirect_uri + "?" + urlencode(params)
        else:
            response = HttpResponse(
                format_html(
                    '<!doctype html><html lang="en"><meta name="viewport" content="width=device-width, initial-scale=1">'
                    "<title>Connect {}</title><main><h1>Connect {}</h1>"
                    "<p>Signed in as {}. Allow this app to access {}?</p>"
                    '<form method="post"><input type="hidden" name="csrfmiddlewaretoken" value="{}">'
                    '<button name="approve" value="yes">Connect app</button> '
                    '<button name="approve" value="no">Cancel</button></form></main></html>',
                    client.app_name,
                    client.app_name,
                    request.user.get_username(),
                    client.consent_description,
                    get_token(request),
                )
            )
        response["Referrer-Policy"] = "no-referrer"
        response["X-Frame-Options"] = "DENY"
        return response

    @csrf_exempt
    @require_http_methods(["POST"])
    def token(request: HttpRequest) -> JsonResponse:
        """PKCE/refresh credentials, never browser cookies, authorize this endpoint."""
        service = factory()
        client = service.client
        data = body(request)
        result = None
        if data.get("client_id") == client.client_id:
            if (
                data.get("grant_type") == "authorization_code"
                and data.get("redirect_uri") == client.redirect_uri
            ):
                result = service.exchange(
                    data.get("code", ""), data.get("code_verifier", "")
                )
            elif data.get("grant_type") == "refresh_token":
                result = service.refresh(data.get("refresh_token", ""))
        response = json_reply(
            result or {"error": "invalid_grant"}, 200 if result else 400
        )
        return response

    @csrf_exempt
    @require_http_methods(["POST"])
    def logout(request: HttpRequest) -> JsonResponse:
        """Revoke the device session without affecting the user's web session."""
        factory().revoke(body(request).get("refresh_token", ""))
        response = json_reply({"revoked": True})
        return response

    return SimpleNamespace(authorize=authorize, token=token, logout=logout)
