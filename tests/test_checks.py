from unittest import mock

import pytest
from django.core.checks import Error, Warning
from django.core.management import call_command
from django.db import connection, models
from django.db.backends.base.base import BaseDatabaseWrapper
from django.test.utils import isolate_apps

from django_sqlite_strict import checks
from django_sqlite_strict.base import DatabaseWrapper
from tests.test_project.models import Legacy


class MacAddressField(models.Field):
    def db_type(self, connection):
        return "macaddr"


class StrictTextField(models.Field):
    def db_type(self, connection):
        return "TEXT"


class GeneratedField(models.Field):
    def db_type(self, connection):
        return None


def test_none_databases_checks_all_configured():
    """databases=None should check all configured databases, not skip all."""
    with isolate_apps("tests") as registry:

        class Printer(models.Model):
            mac_address = MacAddressField()

            class Meta:
                app_label = "tests"

        with mock.patch.object(checks, "apps", registry):
            result = checks.check_column_types(databases=None)

    assert len(result) == 1
    assert result[0].id == "dss.E001"


@pytest.mark.django_db
def test_no_databases_given():
    assert checks.check_column_types(databases=None) == []
    assert checks.check_tables_are_strict(databases=None) == []
    assert checks.check_decimal_max_digits(databases=None) == []


def test_unmapped_column_type_reported():
    with isolate_apps("tests") as registry:

        class Printer(models.Model):
            mac_address = MacAddressField()

            class Meta:
                app_label = "tests"

        with mock.patch.object(checks, "apps", registry):
            (error,) = checks.check_column_types(databases=["default"])

    assert isinstance(error, Error)
    assert error.id == "dss.E001"
    assert error.obj is Printer._meta.get_field("mac_address")
    assert error.msg == (
        "tests.Printer.mac_address has database column type "
        "'macaddr', which STRICT tables do not accept."
    )


def test_valid_column_types_are_ignored():
    with isolate_apps("tests") as registry:

        class Note(models.Model):
            body = StrictTextField()
            generated = GeneratedField()

            class Meta:
                app_label = "tests"

        with mock.patch.object(checks, "apps", registry):
            assert checks.check_column_types(databases=["default"]) == []


@pytest.mark.django_db
def test_all_project_tables_strict():
    assert checks.check_tables_are_strict(databases=["default"]) == []


@pytest.mark.django_db(transaction=True)
def test_non_strict_table_reported():
    table = Legacy._meta.db_table
    with connection.cursor() as cursor:
        cursor.execute(f'DROP TABLE "{table}"')
        cursor.execute(
            f'CREATE TABLE "{table}" ('
            '"id" integer NOT NULL PRIMARY KEY AUTOINCREMENT, '
            '"name" varchar(50) NOT NULL, '
            '"amount" decimal NOT NULL)'
        )

    result = checks.check_tables_are_strict(databases=["default"])

    assert len(result) == 1
    error = result[0]
    assert isinstance(error, Error)
    assert error.id == "dss.E002"
    assert error.msg == f"Table {table!r} of model test_project.Legacy is not STRICT."
    assert error.obj is Legacy

    call_command("convert_to_strict", no_input=True)

    assert checks.check_tables_are_strict(databases=["default"]) == []


@pytest.mark.django_db
def test_missing_table_not_reported():
    with isolate_apps("tests") as registry:

        class Unmigrated(models.Model):
            class Meta:
                app_label = "tests"

        with mock.patch.object(checks, "apps", registry):
            result = checks.check_tables_are_strict(databases=["default"])

    assert result == []


def test_strict_models_skips_non_django_sqlite_strict_connections():
    mock_connection = mock.Mock(spec=BaseDatabaseWrapper)
    mock_connections = {"default": mock_connection}

    with mock.patch.object(checks, "connections", mock_connections):
        # need to materialise the empty generator to check it
        assert list(checks._strict_models(databases=["default"])) == []


def test_unmanaged_models_are_ignored():
    with isolate_apps("tests") as registry:

        class Printer(models.Model):
            mac_address = MacAddressField()

            class Meta:
                app_label = "tests"
                managed = False

        with mock.patch.object(checks, "apps", registry):
            assert checks.check_column_types(databases=["default"]) == []


def test_proxy_models_are_ignored():
    with isolate_apps("tests") as registry:

        class Printer(models.Model):
            mac_address = MacAddressField()

            class Meta:
                app_label = "tests"

        class PrinterProxy(Printer):
            class Meta:
                proxy = True
                app_label = "tests"

        with mock.patch.object(checks, "apps", registry):
            result = checks.check_column_types(databases=["default"])

    (error,) = result
    assert error.obj is Printer._meta.get_field("mac_address")


def test_router_can_exclude_models():
    with isolate_apps("tests") as registry:

        class Printer(models.Model):
            mac_address = MacAddressField()

            class Meta:
                app_label = "tests"

        with (
            mock.patch.object(checks, "apps", registry),
            mock.patch.object(
                checks.router,
                "allow_migrate_model",
                return_value=False,
            ),
        ):
            assert checks.check_column_types(databases=["default"]) == []


def test_wide_decimal_field_warned():
    with isolate_apps("tests") as registry:

        class Account(models.Model):
            amount = models.DecimalField(max_digits=20, decimal_places=4)

            class Meta:
                app_label = "tests"

        with mock.patch.object(checks, "apps", registry):
            result = checks.check_decimal_max_digits(databases=["default"])

    assert len(result) == 1
    warning = result[0]
    assert isinstance(warning, Warning)
    assert warning.id == "dss.W001"
    assert warning.msg == (
        "tests.Account.amount has DecimalField(max_digits=20), "
        "but SQLite STRICT stores decimals as REAL, which maxes out "
        "at 15 significant digits."
    )


def test_exempt_tables_skipped():
    with isolate_apps("tests") as registry:

        class Printer(models.Model):
            mac = MacAddressField()
            ink_ml = models.DecimalField(max_digits=20, decimal_places=4)

            class Meta:
                app_label = "tests"

        mock_connection = mock.Mock(spec=DatabaseWrapper)
        mock_connection.strict_exempt_tables = frozenset({Printer._meta.db_table})
        mock_connections = {"default": mock_connection}

        with (
            mock.patch.object(checks, "apps", registry),
            mock.patch.object(checks, "connections", mock_connections),
        ):
            assert checks.check_column_types(databases=["default"]) == []
            assert checks.check_decimal_max_digits(databases=["default"]) == []
