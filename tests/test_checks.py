from unittest import mock

import pytest
from django.core.checks import Error
from django.db import models
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


def test_no_databases_given():
    assert checks.check_column_types(databases=None) == []


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
