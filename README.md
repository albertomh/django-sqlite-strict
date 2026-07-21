# django-sqlite-strict

## Usage

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
