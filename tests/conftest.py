from collections.abc import Callable, Generator

import pytest
from django.core.management import call_command
from django.db import connection, models


@pytest.fixture
def legacy_sql_table():
    with connection.cursor() as cursor:
        cursor.execute("""
            CREATE TABLE legacy_sql (
                id integer primary key,
                value text
            )
        """)

    try:
        yield
    finally:
        with connection.cursor() as cursor:
            cursor.execute("DROP TABLE IF EXISTS legacy_sql")


@pytest.fixture
def non_strict_table() -> Generator[Callable[[type[models.Model]], None], None, None]:
    """
    Recreate a model's database table as a non-STRICT SQLite table.

    This simulates legacy SQLite tables so the STRICT conversion command can
    be tested. Existing rows are preserved so tests can verify that schema
    features survive conversion.
    """

    remade: list[type[models.Model]] = []

    def recreate(model: type[models.Model]) -> None:
        table = model._meta.db_table

        with connection.cursor() as cursor:
            cursor.execute(f'SELECT * FROM "{table}"')
            rows = cursor.fetchall()
            columns = [column[0] for column in cursor.description]

        with connection.schema_editor() as editor:
            editor.sql_create_table = "CREATE TABLE %(table)s (%(definition)s)"
            editor.delete_model(model)
            editor.create_model(model)

        if rows:
            quoted_columns = ", ".join(
                connection.ops.quote_name(column) for column in columns
            )
            placeholders = ", ".join(["%s"] * len(columns))

            with connection.cursor() as cursor:
                cursor.executemany(
                    f"""
                    INSERT INTO {connection.ops.quote_name(table)}
                    ({quoted_columns})
                    VALUES ({placeholders})
                    """,
                    rows,
                )

        remade.append(model)

    yield recreate

    if remade:
        call_command("convert_to_strict", no_input=True, stdout=open("/dev/null", "w"))
