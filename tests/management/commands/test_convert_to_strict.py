from decimal import Decimal

import pytest
from django.core.management import CommandError, call_command
from django.db import connection

from tests.test_project.models import Legacy
from tests.utils import non_strict_tables


@pytest.mark.django_db(transaction=True)
def test_convert_to_strict_rejects_non_sqlite_database():
    with pytest.raises(CommandError, match="'other' is not a SQLite database"):
        call_command("convert_to_strict", database="other", no_input=True)


@pytest.mark.django_db(transaction=True)
def test_convert_to_strict_is_idempotent(capsys):
    call_command("convert_to_strict")
    assert non_strict_tables() == []

    call_command("convert_to_strict")

    assert "All tables are already STRICT." in capsys.readouterr().out
    assert non_strict_tables() == []


@pytest.mark.django_db(transaction=True)
def test_convert_to_strict_rebuilds_legacy_tables():
    table = Legacy._meta.db_table

    with connection.cursor() as cursor:
        cursor.execute(f'DROP TABLE "{table}"')
        cursor.execute(
            f'CREATE TABLE "{table}" ('
            '"id" integer NOT NULL PRIMARY KEY AUTOINCREMENT, '
            '"name" varchar(50) NOT NULL, '
            '"amount" decimal NOT NULL)'
        )
        cursor.execute(
            f'INSERT INTO "{table}" ("name", "amount") VALUES (%s, %s)',
            ["kept", "19.99"],
        )

    assert non_strict_tables() == [table]

    call_command("convert_to_strict", no_input=True)

    assert non_strict_tables() == []

    obj = Legacy.objects.get()
    assert (obj.name, obj.amount) == ("kept", Decimal("19.99"))


@pytest.mark.django_db(transaction=True)
def test_convert_to_strict_skips_unknown_tables(legacy_sql_table, capsys):
    assert sorted(non_strict_tables()) == ["legacy_sql"]

    call_command("convert_to_strict", no_input=True)

    assert "Skipped legacy_sql" in capsys.readouterr().out
    assert non_strict_tables() == ["legacy_sql"]

    with connection.cursor() as cursor:
        cursor.execute("SELECT value FROM legacy_sql")
        assert cursor.fetchall() == []
