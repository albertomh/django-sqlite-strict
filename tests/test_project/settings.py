SECRET_KEY = "django-insecure_test-only"
USE_TZ = True
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

INSTALLED_APPS = [
    "django.contrib.contenttypes",
    "django.contrib.auth",
    "django_sqlite_strict",
    "tests.test_project",
]

DATABASES = {
    "default": {
        "ENGINE": "django_sqlite_strict",
        "NAME": ":memory:",
    }
}
