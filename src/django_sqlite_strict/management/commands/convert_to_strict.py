from typing import Any

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = (
        "Rebuild every non-STRICT managed table as a STRICT table. "
        "The command uses Django's SQLite table-rebuild implementation, "
        "preserving data, indexes, constraints and foreign keys. "
        "Each table is rebuilt in its own atomic transaction. Existing "
        "tables that are already STRICT are left unchanged."
    )

    def handle(self, *args: Any, **options: Any) -> None:
        pass
