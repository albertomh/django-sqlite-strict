# django-sqlite-strict

## Usage

`django-sqlite-strict` is a drop-in replacement for Django's stock SQLite engine.

### Prerequisites

- A Django webapp using:
  - Django >= 4.2
  - SQLite >= 3.37.0

### Install

1. Add as a dependency with `uv add django-sqlite-strict`
2. In `settings.py`, add to `INSTALLED_APPS` after any first-party apps and before `django.contrib`
   packages.
3. In `settings.py`, configure DATABASES to use it as the engine:

```python
DATABASES = {
    "default": {
        "ENGINE": "django_sqlite_strict",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}
```

## Develop

### Run tests

```sh
# run latest supported python/django pairing eg. 3.14/6.0
uvx nox

# run all test sessions
uvx nox -s test
```
