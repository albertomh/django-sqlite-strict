# django-sqlite-strict

<!-- markdownlint-disable MD013 line-length -->
![python >= 3.10](https://img.shields.io/badge/>=3.10-4584b6?logo=python&logoColor=ffde57&style=flat-square)
[![Django](https://img.shields.io/badge/Django-092E20?logo=django&logoColor=ffffff&style=flat-square)](https://docs.djangoproject.com/en/stable/)
[![SQLite](https://img.shields.io/badge/SQLite-ffffff?logo=sqlite&logoColor=0f80cc&style=flat-square)](https://www.sqlite.org/docs.html)
[![prek](https://img.shields.io/badge/prek-CC5A23?logo=prek&logoColor=FFFFFF&style=flat-square)](https://github.com/j178/prek)
[![pytest](https://img.shields.io/badge/pytest-0A9EDC?logo=pytest&logoColor=white&style=flat-square)](https://github.com/pytest-dev/pytest)
[![nox](https://img.shields.io/badge/%F0%9F%A6%8A-Nox-D85E00.svg?style=flat-square)](https://github.com/wntrblm/nox)
[![coverage](https://img.shields.io/badge/😴_coverage-59aabd?style=flat-square)](https://coverage.readthedocs.io/)
[![GitHub Actions Workflow Status](https://img.shields.io/github/actions/workflow/status/albertomh/django-sqlite-strict/ci.yaml?style=flat-square&logo=github&label=CI&labelColor=000000)](https://github.com/albertomh/django-sqlite-strict/actions/workflows/ci.yaml)
[![PyPI Version](https://img.shields.io/pypi/v/django-sqlite-strict?style=flat-square&labelColor=0073b7&color=0073b7&label=📦%20PyPI&cachebust=1785060266)](https://pypi.org/project/django-sqlite-strict/)
<!-- markdownlint-enable MD013 line-length -->

`django-sqlite-strict` is a drop-in replacement for Django's stock SQLite engine that enforces
STRICT tables.

## Prerequisites

`django-sqlite-strict` works on Django webapps that use:

- Django >= 4.2
- SQLite >= 3.37.0

## Install

1. Add as a dependency:

    ```sh
    uv add django-sqlite-strict
    ```

1. In `settings.py`, add to `INSTALLED_APPS` after any first-party apps and before
`django.contrib` packages.

    ```python
    INSTALLED_APPS = [
        ...,
        'django_sqlite_strict',
        ...,
    ]
    ```

1. In `settings.py`, configure DATABASES to use it as the engine:

    ```python
    DATABASES = {
        "default": {
            "ENGINE": "django_sqlite_strict",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }
    ```

## Features

### Compared to Django's stock SQLite backend

SQLite `STRICT` tables only permit the storage classes `INTEGER`, `REAL`, `TEXT`, `BLOB` and `ANY`
([source](https://www.sqlite.org/stricttables.html)).  
To generate valid `STRICT` tables, `django-sqlite-strict` maps field types differently to Django's
stock SQLite backend. For example:

- `CharField` is stored as `TEXT` instead of `VARCHAR`  
- `BooleanField` as `INTEGER` instead of `BOOL`  
- `DecimalField` as `REAL` instead of `DECIMAL`

These changes affect only the SQL column types used in migrations, Django's Python field API
remains unchanged.

> [!WARNING]
> Because of the above `STRICT`-compliant field type mappings, `DecimalField` is stored as `REAL`.  
> Applications requiring exact decimal arithmetic should consider storing integer minor units or
> using a database with native DECIMAL support.

### System checks

`django-sqlite-strict` will register the following [Django system checks](https://docs.djangoproject.com/en/stable/topics/checks/):

- [`check_column_types`](./src/django_sqlite_strict/checks.py#L31)  
  Raises an error if any entry in the `DATABASES` setting has a column of a type that is not
  accepted by STRICT tables.

## Develop

### Development prerequisites

The following tools must be available locally to develop `django-sqlite-strict`:

- [uv](https://docs.astral.sh/uv/)
- [prek](https://prek.j178.dev/)

### Run tests

The project aims for 100% test coverage. `nox` is used to run the test suite against
all supported Python/Django pairings (see [`noxfile.py`](./noxfile.py#L5)).

```sh
# run latest supported Python/Django pairing only
# (eg. Python 3.14 / Django 6.0)
uvx nox

# run all test sessions
# (ie. all supported Python/Django pairings)
uvx nox -s test
```

### Use the development version in projects

Build the package as a binary distribution (wheel) and install it in a Django project:

```sh
# from django-sqlite-strict's root directory
uv build

# in the target Django webapp project
uv add ~/Projects/django-sqlite-strict/dist/django_sqlite_strict-M.m.p-py3-none-any.whl
```

---

## Acknowledgements

<!-- markdownlint-disable MD033 no-inline-html -->
<!-- markdownlint-disable MD013 line-length -->
This package was inspired by Martin Dørum's advocacy for STRICT tables in the article
<a href="https://mort.coffee/home/sqlite-editions/" target="_blank">SQLite should have (Rust-style) editions</a>.
<!-- markdownlint-enable MD013 line-length -->
<!-- markdownlint-enable MD033 no-inline-html -->

---

## Shameless self-promotion

Starting a new Django project? Try [djereo](https://github.com/albertomh/djereo) for a Django
project template with modern defaults.

Try [pycliché](https://github.com/albertomh/pycliche/) for a no-nonsense Python project template
with opinionated tooling.

---

<!-- markdownlint-disable MD033 no-inline-html -->
<figure align="center">
  <!-- markdownlint-disable MD013 line-length -->
  <img
    src="docs/eton_birching_block.jpg"
    alt=""
    width=400px/>
  <figcaption>19th century apparatus to enforce STRICT columns (<a href="https://catalogue.etoncollege.com/object-pa-a-142-113-2014" target="_blank">source</a>, Eton College)</figcaption>
  <!-- markdownlint-enable MD013 line-length -->
</figure>
<!-- markdownlint-enable MD033 no-inline-html -->
