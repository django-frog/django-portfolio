# portfolio/settings/prod.py
from .base import *
from django.core.exceptions import ImproperlyConfigured
import dj_database_url

DEBUG = False
ALLOWED_HOSTS = [
    'localhost',
    'mohammadasdjangodev.pythonanywhere.com',
    'django-portfolio-yuuf.onrender.com',
    '.onrender.com',
]

_db_config = dj_database_url.config(
    conn_max_age=600,
    conn_health_checks=True,
)
if not _db_config or 'ENGINE' not in _db_config:
    raise ImproperlyConfigured(
        "DATABASE_URL is not set. Provision a PostgreSQL database on Render "
        "(Dashboard -> New -> PostgreSQL) or set DATABASE_URL to a "
        "postgres:// connection string in the environment."
    )

DATABASES = {'default': _db_config}

print("🏭 Running in PRODUCTION mode (PostgreSQL)")
