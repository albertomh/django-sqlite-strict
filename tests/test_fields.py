from decimal import Decimal

import pytest
from django.core.checks import Error
from django.db import connection, models
from django.test.utils import isolate_apps

from django_sqlite_strict import checks
from django_sqlite_strict.fields import StrictDecimalField
from tests.test_project.models import Order


@pytest.mark.django_db
def test_strict_decimal_field_stored_as_scaled_integer():
    obj = Order.objects.create(total_price=Decimal("19.99"))

    with connection.cursor() as cursor:
        cursor.execute(
            f'SELECT "total_price", typeof("total_price") '
            f'FROM "{Order._meta.db_table}" WHERE id = %s',
            [obj.pk],
        )
        raw, storage_class = cursor.fetchone()

    assert (raw, storage_class) == (1999, "integer")


@pytest.mark.parametrize("test_input", [Decimal("1234567890123456.78"), None])
@pytest.mark.django_db
def test_strict_decimal_field_round_trips(test_input):
    obj = Order.objects.create(total_price=test_input)
    obj.refresh_from_db()

    assert obj.total_price == test_input


@pytest.mark.django_db
def test_strict_decimal_field_rejects_excess_decimal_places():
    with pytest.raises(ValueError, match=r"19\.999"):
        Order.objects.create(total_price=Decimal("19.999"))


@pytest.mark.django_db
def test_strict_decimal_field_lookups_and_ordering():
    for raw in ("1.00", "19.99", "20.00", "-3.50"):
        Order.objects.create(total_price=Decimal(raw))

    total_prices = Order.objects.values_list("total_price", flat=True)

    assert Order.objects.filter(total_price__exact=Decimal("19.99")).count() == 1
    assert set(total_prices.filter(total_price__gt=Decimal("19.99"))) == {
        Decimal("20.00")
    }
    assert set(total_prices.filter(total_price__gte=Decimal("19.99"))) == {
        Decimal("19.99"),
        Decimal("20.00"),
    }
    assert list(total_prices.order_by("total_price")) == [
        Decimal("-3.50"),
        Decimal("1.00"),
        Decimal("19.99"),
        Decimal("20.00"),
    ]


@pytest.mark.django_db
def test_strict_decimal_field_sum_is_exact():
    Order.objects.create(total_price=Decimal("1234567890123456.78"))
    Order.objects.create(total_price=Decimal("0.01"))

    total = Order.objects.aggregate(total=models.Sum("total_price"))["total"]

    assert total == Decimal("1234567890123456.79")


@pytest.mark.django_db
def test_strict_decimal_field_avg_with_output_field_is_scaled_decimal():
    Order.objects.create(total_price=Decimal("19.99"))
    Order.objects.create(total_price=Decimal("20.01"))
    output_field = StrictDecimalField(max_digits=18, decimal_places=2)

    average = Order.objects.aggregate(
        avg=models.Avg("total_price", output_field=output_field)
    )["avg"]

    assert isinstance(average, Decimal)
    assert average == Decimal("20.00")


def test_strict_decimal_field_reports_int64_overflow_risk():
    with isolate_apps("tests"):

        class Wide(models.Model):
            total_price = StrictDecimalField(max_digits=19, decimal_places=2)

            class Meta:
                app_label = "tests"

        errors = Wide._meta.get_field("total_price").check()

    assert len(errors) == 1
    error = errors[0]
    assert isinstance(error, Error)
    assert error.id == "dss.E003"
    assert error.msg == (
        "StrictDecimalField must have max_digits <= 18, or its integer minor "
        "units could overflow SQLite's 8-byte INTEGER."
    )


def test_strict_decimal_field_accepts_values_within_int64():
    assert Order._meta.get_field("total_price").check() == []


def test_strict_decimal_field_ignores_invalid_max_digits_in_int64_check():
    field = StrictDecimalField(max_digits=None, decimal_places=2)

    assert field._check_max_digits_fit_int64() == []


def test_strict_decimal_field_preserves_expressions_for_prep():
    expression = models.F("total_price")
    field = Order._meta.get_field("total_price")

    assert field.get_prep_value(expression) is expression


def test_strict_decimal_field_scales_float_database_values():
    field = Order._meta.get_field("total_price")

    assert field.from_db_value(2000.0, None, connection) == Decimal("20.00")


@pytest.mark.django_db
def test_strict_decimal_field_column_type_is_integer_and_checks_pass():
    assert Order._meta.get_field("total_price").db_type(connection) == "integer"
    assert checks.check_column_types(databases=["default"]) == []
    assert checks.check_decimal_max_digits(databases=["default"]) == []


def test_strict_decimal_field_deconstruct_round_trips():
    """Test StrictDecimalField survives a migration serialise/deserialise round-trip."""
    field = StrictDecimalField(max_digits=18, decimal_places=2, null=True)

    _name, path, args, kwargs = field.deconstruct()
    clone = StrictDecimalField(*args, **kwargs)

    assert path == "django_sqlite_strict.fields.StrictDecimalField"
    assert kwargs == {"max_digits": 18, "decimal_places": 2, "null": True}
    assert clone.deconstruct()[1:] == (path, args, kwargs)
