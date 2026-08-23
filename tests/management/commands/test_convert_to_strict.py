import pytest
from django.core.management import CommandError, call_command

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
