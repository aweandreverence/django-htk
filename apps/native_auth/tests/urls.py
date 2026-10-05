# Django Imports
from django.http import HttpResponse
from django.urls import path

# HTK Imports
from htk.apps.native_auth.config import NativeClient
from htk.apps.native_auth.services import NativeAuthService
from htk.apps.native_auth.views import build_views


def client(name="alpha"):
    return NativeClient(name, name + "://auth/callback", name.title(), "login")


def service(name="alpha"):
    return NativeAuthService(client(name))


alpha = build_views(service)
beta = build_views(lambda: service("beta"))
urlpatterns = [
    path("login", lambda request: HttpResponse("Login"), name="login")
]
for name, views in [("alpha", alpha), ("beta", beta)]:
    urlpatterns += [
        path(name + "/authorize", views.authorize),
        path(name + "/token", views.token),
        path(name + "/logout", views.logout),
    ]
