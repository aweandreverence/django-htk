# Django Imports
from django.apps import AppConfig


class NativeAuthConfig(AppConfig):
    name = "htk.apps.native_auth"
    label = "native_auth"
    verbose_name = "Native device authentication"
    default_auto_field = "django.db.models.BigAutoField"
