import pytest
from django.core.management import call_command

from tests.utils import non_strict_tables


@pytest.mark.django_db(transaction=True)
def test_convert_to_strict_is_idempotent(capsys):
    call_command("convert_to_strict")
    assert non_strict_tables() == []

    call_command("convert_to_strict")

    assert "All tables are already STRICT." in capsys.readouterr().out
    assert non_strict_tables() == []
