"""Small private JSON boundaries without application/model dependencies."""

# Python Standard Library Imports
import json

# Django Imports
from django.http import (
    HttpRequest,
    JsonResponse,
)


def private_json_response(payload: dict, status: int = 200) -> JsonResponse:
    """Keep account and library data out of intermediary caches."""
    response = JsonResponse(payload, status=status)
    response["Cache-Control"] = "no-store"
    response["Referrer-Policy"] = "no-referrer"
    return response


def parse_string_json_body(request: HttpRequest) -> dict:
    """Reject oversized and non-object JSON before processing credentials."""
    value = {}
    if len(request.body) <= 16384:
        try:
            parsed = json.loads(request.body)
            if isinstance(parsed, dict) and all(
                isinstance(v, str) for v in parsed.values()
            ):
                value = parsed
        except (ValueError, UnicodeDecodeError):
            pass
    return value
