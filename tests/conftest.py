import pytest
from django.db import connection


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
