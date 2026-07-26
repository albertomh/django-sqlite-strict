from django.apps import AppConfig
from django.core.checks import Tags, register

from django_sqlite_strict import checks


class DjangoSqliteStrictConfig(AppConfig):
    name = "django_sqlite_strict"
    verbose_name = "django-sqlite-strict"

    def ready(self) -> None:
        register(Tags.database)(checks.check_column_types)
