# ruff: noqa: TRY003

"""
Drop-in replacement for `django.db.backends.sqlite3` that creates all
tables as STRICT tables <https://www.sqlite.org/stricttables.html>.

Usage:
```python
    DATABASES = {"default": {"ENGINE": "django_sqlite_strict", "NAME": ...}}
```
"""

from typing import Any, ClassVar

from django.core.exceptions import ImproperlyConfigured
from django.db.backends.sqlite3 import base, schema
from django.db.models import Model
from django.db.utils import DEFAULT_DB_ALIAS

STRICT_DATA_TYPES = {
    "BigIntegerField": "integer",
    "BooleanField": "integer",
    # STRICT tables don't permit VARCHAR, so use TEXT instead
    "CharField": "text",
    "DateField": "text",
    "DateTimeField": "text",
    "DecimalField": "real",
    "DurationField": "integer",
    "FileField": "text",
    "FilePathField": "text",
    "GenericIPAddressField": "text",
    "IPAddressField": "text",
    "PositiveBigIntegerField": "integer",
    "PositiveIntegerField": "integer",
    "PositiveSmallIntegerField": "integer",
    "SlugField": "text",
    "SmallIntegerField": "integer",
    "TimeField": "text",
    "UUIDField": "text",
}


if base.Database.sqlite_version_info < (3, 37, 0):
    message = (
        "django_sqlite_strict requires SQLite 3.37.0 or later "
        f"(found {base.Database.sqlite_version})."
    )
    raise ImproperlyConfigured(message)


class DatabaseSchemaEditor(schema.DatabaseSchemaEditor):
    sql_create_table = "CREATE TABLE %(table)s (%(definition)s) STRICT"

    def table_sql(self, model: type[Model]) -> tuple[str, list[Any]]:
        table = model._meta.db_table
        exempt = self.connection.strict_exempt_tables
        # _remake_table rebuilds through a shadow model whose table is named
        # "new__<table>", so match exemptions under that prefix too.
        if table not in exempt and table.removeprefix("new__") not in exempt:
            return super().table_sql(model)
        original = self.sql_create_table
        self.sql_create_table = schema.DatabaseSchemaEditor.sql_create_table
        try:
            return super().table_sql(model)
        finally:
            self.sql_create_table = original


class DatabaseWrapper(base.DatabaseWrapper):
    SchemaEditorClass = DatabaseSchemaEditor

    # STRICT tables accept only INT, INTEGER, REAL, TEXT, BLOB and ANY as column types.
    # Replace Django's usual SQLite aliases (eg. VARCHAR, BOOL, DECIMAL) with
    # their STRICT equivalents so migrations generate valid STRICT tables.
    # DecimalField uses REAL because STRICT tables do not allow NUMERIC.
    data_types: ClassVar = {
        **base.DatabaseWrapper.data_types,
        **STRICT_DATA_TYPES,
    }

    def __init__(
        self, settings_dict: dict[str, Any], alias: str = DEFAULT_DB_ALIAS
    ) -> None:
        options = settings_dict.get("OPTIONS") or {}
        exempt_tables = options.get("strict_exempt_tables", ())
        if isinstance(exempt_tables, str):
            raise ImproperlyConfigured(
                "'strict_exempt_tables' must be an iterable of table names,"
                " not a single string."
            )
        # tables created with the stock non-STRICT template
        self.strict_exempt_tables = frozenset(exempt_tables)
        super().__init__(settings_dict, alias)

    def get_connection_params(self) -> dict[str, Any]:
        conn_params = super().get_connection_params()
        conn_params.pop("strict_exempt_tables", None)
        return conn_params
