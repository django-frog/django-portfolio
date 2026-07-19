# portfolio/settings/prod.py
from .base import *
import dj_database_url

DEBUG = False
ALLOWED_HOSTS = [
    'localhost',
    'mohammadasdjangodev.pythonanywhere.com',
    'django-portfolio-yuuf.onrender.com',
    '.onrender.com',
]

DATABASES = {
    'default': dj_database_url.config(
        conn_max_age=600,
        conn_health_checks=True,
    )
}

print("🏭 Running in PRODUCTION mode (PostgreSQL)")
