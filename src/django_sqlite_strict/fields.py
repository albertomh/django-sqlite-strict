from decimal import Decimal
from typing import Any

from django.core import checks
from django.db import models

MAX_INT64_DIGITS = 18


class StrictDecimalField(models.DecimalField):
    """
    Store exact decimal values as integer minor units in an INTEGER column.

    For example, Decimal("19.99") with decimal_places=2 is stored as 1999
    and read back as Decimal("19.99").
    """

    def db_type(self, connection: Any) -> str:
        return "integer"

    def get_internal_type(self) -> str:
        # Avoid SQLite's DecimalField converter, which uses a 15-digit float
        # context before from_db_value() can scale the stored integer.
        return "BigIntegerField"

    def check(self, **kwargs: Any) -> list[checks.CheckMessage]:
        return [*super().check(**kwargs), *self._check_max_digits_fit_int64()]

    def _check_max_digits_fit_int64(self) -> list[checks.CheckMessage]:
        try:
            max_digits = int(self.max_digits)
        except (TypeError, ValueError):
            # DecimalField.check() already reports invalid max_digits values
            return []
        if max_digits <= MAX_INT64_DIGITS:
            return []
        return [
            checks.Error(
                f"StrictDecimalField must have max_digits <= {MAX_INT64_DIGITS}, "
                "or its integer minor units could overflow SQLite's 8-byte INTEGER.",
                hint=(
                    f"Use max_digits <= {MAX_INT64_DIGITS} or store the value as text."
                ),
                obj=self,
                id="dss.E003",
            )
        ]

    def get_prep_value(self, value: Any) -> Any:
        if value is None:
            return None
        if hasattr(value, "resolve_expression"):
            return value
        value = self.to_python(value)
        scaled = value.scaleb(self.decimal_places)
        if scaled != scaled.to_integral_value():
            raise ValueError(  # noqa: TRY003
                f"Field '{self.name}' expected a value with at most "
                f"{self.decimal_places} decimal places, got {value}."
            )
        return int(scaled)

    def get_db_prep_value(
        self, value: Any, connection: Any, prepared: bool = False
    ) -> Any:
        if not prepared:
            value = self.get_prep_value(value)
        return value

    def get_db_prep_save(self, value: Any, connection: Any) -> Any:
        return self.get_db_prep_value(value, connection=connection, prepared=False)

    def from_db_value(
        self, value: Any, expression: Any, connection: Any
    ) -> Decimal | None:
        if value is None:
            return None
        if isinstance(value, float):
            value = str(value)
        return Decimal(value).scaleb(-self.decimal_places)
