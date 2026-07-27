"""
Drop-in replacement for `django.db.backends.sqlite3` that creates all
tables as STRICT tables <https://www.sqlite.org/stricttables.html>.

Usage:
```python
    DATABASES = {"default": {"ENGINE": "django_sqlite_strict", "NAME": ...}}
```
"""

from typing import ClassVar

from django.core.exceptions import ImproperlyConfigured
from django.db.backends.sqlite3 import base, schema

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
