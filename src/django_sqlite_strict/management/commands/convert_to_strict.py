# ruff: noqa: TRY003

from argparse import ArgumentParser
from typing import Any, ClassVar

from django.apps import apps
from django.core.management.base import BaseCommand, CommandError
from django.db import DEFAULT_DB_ALIAS, DatabaseError, connections
from django.db.migrations.recorder import MigrationRecorder
from django.db.models import Model

from django_sqlite_strict.base import (
    DatabaseSchemaEditor,
    DatabaseWrapper,
)


class Command(BaseCommand):
    requires_system_checks: ClassVar[list[str]] = []
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
            "--dry-run",
            action="store_true",
            help="List the tables that would be rebuilt and exit.",
        )
        parser.add_argument(
            "--no-input",
            action="store_true",
            help="Do not prompt for confirmation.",
        )

    def handle(self, *args: Any, **options: Any) -> None:
        connection = connections[options["database"]]

        if connection.settings_dict["ENGINE"] != "django_sqlite_strict":
            raise CommandError(
                f"{options['database']!r} is not a django_sqlite_strict database."
            )

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

        # exempt tables are meant to stay non-STRICT, so don't rebuild them
        exempted = sorted(non_strict_tables.intersection(connection.strict_exempt_tables))
        non_strict_tables -= connection.strict_exempt_tables

        if not non_strict_tables and not exempted:
            self.stdout.write(self.style.SUCCESS("All tables are already STRICT."))
            return

        models_by_table = {
            model._meta.db_table: model
            for model in apps.get_models(include_auto_created=True)
            if model._meta.managed and not model._meta.proxy
        }

        # django_migrations is managed by Django but has no AppConfig model.
        recorder = MigrationRecorder.Migration
        models_by_table.setdefault(recorder._meta.db_table, recorder)

        rebuild = [
            models_by_table[name]
            for name in sorted(non_strict_tables)
            if name in models_by_table
        ]
        skipped = sorted(non_strict_tables - models_by_table.keys())

        if options["dry_run"]:
            self._write_dry_run(rebuild, skipped, exempted)
            return

        if not rebuild:
            self._write_skipped(skipped, exempted)
            self.stdout.write(
                self.style.SUCCESS("Successfully rebuilt 0 table(s) as STRICT.")
            )
            return

        self.stdout.write(
            self.style.WARNING(
                f"{len(rebuild)} table(s) will be rebuilt as STRICT tables."
            )
        )

        if skipped:
            self.stdout.write(
                self.style.WARNING(
                    f"{len(skipped)} table(s) will be skipped because they are "
                    "not managed by Django."
                )
            )

        if not self._confirmed(options):
            return

        self._rebuild_tables(connection, rebuild)
        self._write_skipped(skipped, exempted)

        self.stdout.write(
            self.style.SUCCESS(f"Successfully rebuilt {len(rebuild)} table(s) as STRICT.")
        )

    def _write_dry_run(
        self,
        rebuild: list[type[Model]],
        skipped: list[str],
        exempted: list[str],
    ) -> None:
        for model in rebuild:
            self.stdout.write(f"Would rebuild {model._meta.db_table}")
        for table in skipped:
            self.stdout.write(
                self.style.WARNING(f"Would skip {table} (no managed Django model)")
            )
        for table in exempted:
            self.stdout.write(
                self.style.WARNING(f"Would skip {table} (strict_exempt_tables)")
            )

    def _write_skipped(self, skipped: list[str], exempted: list[str]) -> None:
        for table in skipped:
            self.stdout.write(
                self.style.WARNING(f"Skipped {table}: no managed Django model.")
            )
        for table in exempted:
            self.stdout.write(
                self.style.WARNING(
                    f"Skipped {table}: exempted via 'strict_exempt_tables'."
                )
            )

    def _confirmed(self, options: dict[str, Any]) -> bool:
        if options["no_input"]:
            return True
        if input("Continue? [y/N] ").strip().lower() in {"y", "yes"}:
            return True
        self.stdout.write("Aborted.")
        return False

    def _rebuild_tables(
        self, connection: DatabaseWrapper, rebuild: list[type[Model]]
    ) -> None:
        for model in rebuild:
            table = model._meta.db_table
            self.stdout.write(f"Rebuilding {table} ... ", ending="")

            try:
                with DatabaseSchemaEditor(connection, atomic=False) as editor:
                    editor._remake_table(model)
            except DatabaseError:
                self.stdout.write(self.style.ERROR("FAILED"))
                raise

            self.stdout.write(self.style.SUCCESS("OK"))
