from django_sqlite_strict import checks


def test_no_databases_given():
    assert checks.check_column_types(databases=None) == []


def test_project_models_pass():
    assert checks.check_column_types(databases=["default"]) == []
