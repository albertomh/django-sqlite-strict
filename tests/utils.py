import copy
from typing import Any

from django.db import connection
from django.db.backends.base.base import BaseDatabaseWrapper

from django_sqlite_strict.base import DatabaseWrapper


def make_wrapper(
    wrapper_class: type[DatabaseWrapper] = DatabaseWrapper, **options: Any
) -> DatabaseWrapper:
    """A wrapper for an isolated in-memory database, built from the default
    alias' settings plus extra OPTIONS."""
    settings_dict = copy.deepcopy(connection.settings_dict)
    settings_dict["NAME"] = ":memory:"
    settings_dict["OPTIONS"] = {**settings_dict["OPTIONS"], **options}
    return wrapper_class(settings_dict, alias="probe")


def close_wrapper(wrapper: BaseDatabaseWrapper) -> None:
    """Fully close isolated in-memory wrappers created by make_wrapper()."""
    wrapper.validate_thread_sharing()
    if wrapper.connection is not None:
        wrapper._close()
        wrapper.connection = None


def non_strict_tables(wrapper: BaseDatabaseWrapper):
    with wrapper.cursor() as cursor:
        cursor.execute(
            "SELECT name FROM pragma_table_list "
            "WHERE schema = 'main' AND type = 'table' "
            "AND NOT strict AND name NOT LIKE 'sqlite\\_%' ESCAPE '\\'"
        )
        return [row[0] for row in cursor.fetchall()]
