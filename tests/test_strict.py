import uuid
from datetime import date, datetime, time, timedelta, timezone
from decimal import Decimal

import pytest
from django.db import connection, utils

from tests.test_project.models import KitchenSink
from tests.utils import non_strict_tables


@pytest.mark.django_db
def test_all_tables_created_strict():
    assert non_strict_tables() == []


@pytest.mark.django_db
def test_kitchen_sink_round_trip():
    obj = KitchenSink.objects.create(
        big_integer=2**60,
        binary=b"\x00\xff",
        boolean=True,
        char="chars",
        date=date(2026, 7, 17),
        datetime=datetime(2026, 7, 17, 12, 30, 15, 123456, tzinfo=timezone.utc),
        # 15 significant digits limit for SQLite's REAL datatype
        decimal=Decimal("1234567890123.45"),
        duration=timedelta(days=1, seconds=3, microseconds=7),
        floating=0.1,
        generic_ip="2001:db8::1",
        integer=-42,
        json={"nested": ["values", 1, None]},
        positive_big=2**60,
        positive_int=7,
        positive_small=1,
        slug="a-slug",
        small_integer=-3,
        text="body",
        time=time(23, 59, 59),
        uuid=uuid.uuid4(),
    )
    fresh = KitchenSink.objects.get(pk=obj.pk)
    for field in KitchenSink._meta.get_fields():
        if field.concrete and not field.many_to_many:
            expected = getattr(obj, field.attname)
            actual = getattr(fresh, field.attname)
            assert expected == actual, (
                f"Field mismatch in '{field.name}': "
                f"expected {expected!r} ({type(expected).__name__}), "
                f"got {actual!r} ({type(actual).__name__})"
            )


@pytest.mark.django_db
def test_strict_rejects_wrong_storage_class():
    obj = KitchenSink.objects.create(char="x")
    table = KitchenSink._meta.db_table
    with connection.cursor() as cursor, pytest.raises(utils.IntegrityError):
        cursor.execute(
            f'UPDATE "{table}" SET "integer" = %s WHERE id = %s',
            ["not a number", obj.pk],
        )
