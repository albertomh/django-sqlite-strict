from __future__ import annotations

from io import StringIO
from unittest import mock

import pytest
from django.core.exceptions import ImproperlyConfigured
from django.core.management import call_command
from django.db import connection, connections

from tests.test_project.models import KitchenSink, Legacy
from tests.utils import close_wrapper, make_wrapper, non_strict_tables


@pytest.mark.django_db
def test_options_are_not_passed_to_sqlite_connect():
    wrapper = make_wrapper(strict_exempt_tables=["tests_legacy"])
    try:
        # sqlite3.connect() raises TypeError on unknown keyword arguments, so check
        # django-sqlite-strict options were stripped from the parameters.
        with wrapper.cursor() as cursor:
            cursor.execute("SELECT 1")
            assert cursor.fetchone() == (1,)
        assert wrapper.strict_exempt_tables == frozenset({"tests_legacy"})
    finally:
        close_wrapper(wrapper)


def test_exempt_tables_must_not_be_a_single_string():
    with pytest.raises(ImproperlyConfigured):
        make_wrapper(strict_exempt_tables="tests_legacy")


@pytest.mark.django_db
def test_exempt_table_created_non_strict():
    wrapper = make_wrapper(strict_exempt_tables=[Legacy._meta.db_table])
    try:
        with wrapper.schema_editor(atomic=False) as editor:
            editor.create_model(Legacy)
            editor.create_model(KitchenSink)
        assert non_strict_tables(wrapper) == [Legacy._meta.db_table]
    finally:
        close_wrapper(wrapper)


@pytest.mark.django_db
def test_exempt_table_stays_non_strict_through_remake_table():
    wrapper = make_wrapper(strict_exempt_tables=[Legacy._meta.db_table])
    try:
        with wrapper.schema_editor(atomic=False) as editor:
            editor.create_model(Legacy)
        # AlterField-style rebuilds go through a shadow "new__<table>" model
        with wrapper.schema_editor(atomic=False) as editor:
            editor._remake_table(Legacy)
        assert non_strict_tables(wrapper) == [Legacy._meta.db_table]
    finally:
        close_wrapper(wrapper)


@pytest.mark.django_db(transaction=True)
def test_convert_to_strict_skips_exempt_tables():
    table = Legacy._meta.db_table
    with connection.cursor() as cursor:
        cursor.execute(f'DROP TABLE "{table}"')
        cursor.execute(
            f'CREATE TABLE "{table}" ('
            '"id" integer NOT NULL PRIMARY KEY AUTOINCREMENT, '
            '"name" varchar(50) NOT NULL, '
            '"amount" decimal NOT NULL)'
        )
    assert non_strict_tables(connection) == [table]

    out = StringIO()
    with mock.patch.object(
        connections["default"], "strict_exempt_tables", frozenset({table})
    ):
        call_command("convert_to_strict", stdout=out)

    assert non_strict_tables(connection) == [table]
    assert f"Skipped {table}: exempted via 'strict_exempt_tables'." in out.getvalue()

    # rebuild the table STRICT again so other tests see the usual schema
    call_command("convert_to_strict", no_input=True, stdout=StringIO())
    assert non_strict_tables(connection) == []


@pytest.mark.django_db(transaction=True)
def test_convert_to_strict_dry_run_lists_exempt_tables():
    table = Legacy._meta.db_table
    with connection.cursor() as cursor:
        cursor.execute(f'DROP TABLE "{table}"')
        cursor.execute(
            f'CREATE TABLE "{table}" ('
            '"id" integer NOT NULL PRIMARY KEY AUTOINCREMENT, '
            '"name" varchar(50) NOT NULL, '
            '"amount" decimal NOT NULL)'
        )

    out = StringIO()
    with mock.patch.object(
        connections["default"], "strict_exempt_tables", frozenset({table})
    ):
        call_command("convert_to_strict", dry_run=True, no_input=True, stdout=out)

    assert f"Would skip {table} (strict_exempt_tables)" in out.getvalue()

    call_command("convert_to_strict", no_input=True, stdout=StringIO())
    assert non_strict_tables(connection) == []
