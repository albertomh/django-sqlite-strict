import importlib
import sys

import pytest
from django.core.exceptions import ImproperlyConfigured

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
