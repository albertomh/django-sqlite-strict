"""
Drop-in replacement for `django.db.backends.sqlite3` that creates all
tables as STRICT tables <https://www.sqlite.org/stricttables.html>.

Usage:
```python
    DATABASES = {"default": {"ENGINE": "django_sqlite_strict", "NAME": ...}}
```
"""

from django.core.exceptions import ImproperlyConfigured
from django.db.backends.sqlite3 import base

if base.Database.sqlite_version_info < (3, 37, 0):
    message = (
        "django_sqlite_strict requires SQLite 3.37.0 or later "
        f"(found {base.Database.sqlite_version})."
    )
    raise ImproperlyConfigured(message)
