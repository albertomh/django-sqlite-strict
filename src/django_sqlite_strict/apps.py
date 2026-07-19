from django.apps import AppConfig


class DjangoSqliteStrictConfig(AppConfig):
    name = "django_sqlite_strict"
    verbose_name = "django-sqlite-strict"

    def ready(self) -> None:
        print("Using database engine 'django-sqlite-strict'")  # noqa: T201
