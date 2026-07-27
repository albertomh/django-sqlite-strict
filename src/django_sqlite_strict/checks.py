# <https://docs.djangoproject.com/en/stable/topics/checks/>

from collections.abc import Generator

from django.apps import AppConfig, apps
from django.core.checks import CheckMessage, Error, Warning
from django.db import connections, router
from django.db.backends.base.base import BaseDatabaseWrapper
from django.db.models import Model

from django_sqlite_strict.base import DatabaseWrapper
from django_sqlite_strict.constants import REAL_EXACT_DIGITS, STRICT_TYPES


def _strict_models(
    databases: list[str],
) -> Generator[tuple[BaseDatabaseWrapper, type[Model]]]:
    for alias in databases:
        connection = connections[alias]
        if not isinstance(connection, DatabaseWrapper):
            continue
        for model in apps.get_models(include_auto_created=True):
            # skip models we don't create tables for (proxy, swapped, unmanaged)
            if not router.allow_migrate_model(alias, model) or not model._meta.managed:
                continue
            yield connection, model


def check_column_types(
    app_configs: list[AppConfig] | None = None,
    databases: list[str] | None = None,
    **kwargs: object,
) -> list[CheckMessage]:
    errors: list[CheckMessage] = []

    for connection, model in _strict_models(
        databases if databases is not None else list(connections)
    ):
        for field in model._meta.local_fields:
            db_type = field.db_type(connection)
            if db_type is None or db_type.lower() in STRICT_TYPES:
                continue

            errors.append(
                Error(
                    f"{model._meta.label}.{field.name} has database column "
                    f"type {db_type!r}, which STRICT tables do not accept.",
                    hint=(
                        "Use a field that resolves to "
                        + ", ".join([t.upper() for t in STRICT_TYPES])
                        + "or remap it in a DatabaseWrapper subclass."
                    ),
                    obj=field,
                    id="dss.E001",
                )
            )

    return errors


def check_decimal_max_digits(
    app_configs: list[AppConfig] | None = None,
    databases: list[str] | None = None,
    **kwargs: object,
) -> list[CheckMessage]:
    warnings: list[CheckMessage] = []

    for _connection, model in _strict_models(
        databases if databases is not None else list(connections)
    ):
        for field in model._meta.local_fields:
            if field.get_internal_type() != "DecimalField":
                continue
            max_digits = getattr(field, "max_digits", None)
            if max_digits is not None and max_digits > REAL_EXACT_DIGITS:
                warning_message = (
                    f"{model._meta.label}.{field.name} has DecimalField(max_digits={max_digits}), "  # noqa: E501
                    f"but SQLite STRICT stores decimals as REAL, which maxes out "
                    f"at {REAL_EXACT_DIGITS} significant digits."
                )
                hint = (
                    f"Keep max_digits <= {REAL_EXACT_DIGITS}, store integer minor units "
                    "in a BigIntegerField, or switch to a database with DECIMAL support."
                )
                warnings.append(
                    Warning(
                        warning_message,
                        hint=hint,
                        obj=field,
                        id="dss.W001",
                    )
                )

    return warnings
