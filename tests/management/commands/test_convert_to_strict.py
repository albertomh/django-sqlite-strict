from datetime import date
from decimal import Decimal

import pytest
from django import VERSION as DJANGO_VERSION
from django.core.management import CommandError, call_command
from django.db import connection, utils

from tests.test_project.models import Author, Book, Indexed, Legacy, Tag
from tests.utils import non_strict_tables

if DJANGO_VERSION >= (5, 0):
    from tests.test_project.models import GeneratedBook


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
def test_convert_to_strict_dry_run_lists_tables(non_strict_table, capsys):
    non_strict_table(Author)
    non_strict_table(Book)

    call_command("convert_to_strict", dry_run=True, no_input=True)

    out = capsys.readouterr().out
    assert f"Would rebuild {Author._meta.db_table}" in out
    assert f"Would rebuild {Book._meta.db_table}" in out


@pytest.mark.django_db(transaction=True)
def test_convert_to_strict_dry_run_does_not_modify_tables(non_strict_table, capsys):
    non_strict_table(Author)

    call_command("convert_to_strict", dry_run=True, no_input=True)

    assert Author._meta.db_table in non_strict_tables()


@pytest.mark.django_db(transaction=True)
def test_convert_to_strict_dry_run_skips_unknown_tables(legacy_sql_table, capsys):
    call_command("convert_to_strict", dry_run=True, no_input=True)

    out = capsys.readouterr().out
    assert "Would skip legacy_sql (no managed Django model)" in out
    assert non_strict_tables() == ["legacy_sql"]


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


@pytest.mark.django_db(transaction=True)
def test_convert_to_strict_preserves_indexes(non_strict_table):
    Indexed.objects.create(email="a@example.com")

    non_strict_table(Indexed)

    call_command("convert_to_strict", no_input=True)

    with connection.cursor() as cursor:
        cursor.execute(f'PRAGMA index_list("{Indexed._meta.db_table}")')
        indexes = cursor.fetchall()

    assert any(index[2] == 0 for index in indexes)


@pytest.mark.django_db(transaction=True)
def test_convert_to_strict_preserves_unique_constraints(non_strict_table):
    Author.objects.create(name="abc")

    non_strict_table(Author)

    call_command("convert_to_strict", no_input=True)

    with pytest.raises(utils.IntegrityError):
        Author.objects.create(name="abc")


@pytest.mark.django_db(transaction=True)
def test_convert_to_strict_preserves_foreign_keys(non_strict_table):
    non_strict_table(Book)

    call_command("convert_to_strict", no_input=True)

    with pytest.raises(utils.IntegrityError):
        Book.objects.create(author_id=999999)


@pytest.mark.django_db(transaction=True)
def test_convert_to_strict_preserves_many_to_many(non_strict_table):
    non_strict_table(Book.tags.through)

    call_command("convert_to_strict", no_input=True)

    author = Author.objects.create(name="Ray Bradbury")
    book = Book.objects.create(
        author=author,
        published=date(1953, 10, 19),
    )
    tag = Tag.objects.create(name="science-fiction")

    book.tags.add(tag)

    assert list(book.tags.all()) == [tag]


@pytest.mark.django_db(transaction=True)
@pytest.mark.skipif(
    DJANGO_VERSION < (5, 0),
    reason="GeneratedField was introduced in Django 5.0",
)
def test_convert_to_strict_preserves_generated_columns(non_strict_table):
    non_strict_table(Book)

    call_command("convert_to_strict", no_input=True)

    year = 1953
    author = Author.objects.create(name="Ray Bradbury")
    book = GeneratedBook.objects.create(
        author=author,
        published=date(year, 10, 19),
    )
    book.refresh_from_db()

    assert book.year == year
