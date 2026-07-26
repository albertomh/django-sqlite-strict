from unittest import mock

import pytest
from django.core.checks import Error
from django.db import models
from django.db.backends.base.base import BaseDatabaseWrapper
from django.test.utils import isolate_apps

from django_sqlite_strict import checks


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


@pytest.mark.xfail(reason="DatabaseWrapper.data_types needs fleshing out")
def test_project_models_pass():
    assert checks.check_column_types(databases=["default"]) == []


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
