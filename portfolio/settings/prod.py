# portfolio/settings/prod.py
from .base import *

DEBUG = False
ALLOWED_HOSTS = [
    'localhost',
    'mohammadasdjangodev.pythonanywhere.com',
    'django-portfolio-yuuf.onrender.com',
    '.onrender.com',
]

# Production cache and DB already in base
print("🏭 Running in PRODUCTION mode")
