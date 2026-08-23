# ruff: noqa: TRY003

from argparse import ArgumentParser
from typing import Any

from django.core.management.base import BaseCommand, CommandError
from django.db import DEFAULT_DB_ALIAS, connections
from django.db.backends.sqlite3.base import DatabaseWrapper as SQLiteDatabaseWrapper


class Command(BaseCommand):
    help = (
        "Rebuild every non-STRICT managed table as a STRICT table. "
        "The command uses Django's SQLite table-rebuild implementation, "
        "preserving data, indexes, constraints and foreign keys. "
        "Each table is rebuilt in its own atomic transaction. Existing "
        "tables that are already STRICT are left unchanged."
    )

    def add_arguments(self, parser: ArgumentParser) -> None:
        parser.add_argument(
            "--database",
            default=DEFAULT_DB_ALIAS,
            help="Database alias to convert (default: %(default)s).",
        )
        parser.add_argument(
            "--no-input",
            action="store_true",
            help="Do not prompt for confirmation.",
        )

    def handle(self, *args: Any, **options: Any) -> None:
        connection = connections[options["database"]]

        if not isinstance(connection, SQLiteDatabaseWrapper):
            raise CommandError(f"{options['database']!r} is not a SQLite database.")

        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT name
                FROM pragma_table_list
                WHERE schema = 'main'
                  AND type = 'table'
                  AND NOT strict
                  AND name NOT LIKE 'sqlite\\_%' ESCAPE '\\'
                """
            )
            non_strict_tables = {row[0] for row in cursor.fetchall()}

        if not non_strict_tables:
            self.stdout.write(self.style.SUCCESS("All tables are already STRICT."))
            return
