SECRET_KEY = "native-auth-isolated-test-only"
INSTALLED_APPS = [
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "htk.apps.native_auth",
]
DATABASES = {
    "default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}
}
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
USE_TZ = True
ROOT_URLCONF = "htk.apps.native_auth.tests.urls"
ALLOWED_HOSTS = ["testserver"]
MIDDLEWARE = [
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
]
PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]
