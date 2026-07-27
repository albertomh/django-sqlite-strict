import importlib
import sys

import pytest
from django.core.exceptions import ImproperlyConfigured

from django_sqlite_strict.base import DatabaseWrapper
from django_sqlite_strict.constants import STRICT_TYPES

BASE_MODULE = "django_sqlite_strict.base"


def reload_module(module: str):
    sys.modules.pop(module, None)
    return importlib.import_module(module)


def test_incompatible_sqlite_version_raises(mocker):
    mocker.patch(
        "django.db.backends.sqlite3.base.Database.sqlite_version_info", (3, 36, 0)
    )
    with pytest.raises(ImproperlyConfigured, match=r"requires SQLite 3\.37\.0 or later"):
        reload_module(BASE_MODULE)


def test_compatible_sqlite_version_does_not_raise(mocker):
    mocker.patch(
        "django.db.backends.sqlite3.base.Database.sqlite_version_info", (3, 37, 0)
    )
    try:
        reload_module(BASE_MODULE)
    except ImproperlyConfigured:
        pytest.fail("Unexpected ImproperlyConfigured for SQLite 3.37.0")


def test_all_data_types_are_strict_compatible():
    for field_type, sql_type in DatabaseWrapper.data_types.items():
        # resolve dynamic type mappings, eg. `CharField` -> `varchar(max_length)`
        cur_sql_type = sql_type({"max_length": 255}) if callable(sql_type) else sql_type

        # ignore length specifiers, eg. `varchar(255)` -> `varchar`
        base_type = cur_sql_type.partition("(")[0].lower()

        assert base_type in STRICT_TYPES, (
            f"{field_type} maps to non-STRICT type {cur_sql_type!r}"
        )
