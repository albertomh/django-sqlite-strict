import pytest

from tests.utils import non_strict_tables


@pytest.mark.django_db
def test_all_tables_created_strict():
    assert non_strict_tables() == []
