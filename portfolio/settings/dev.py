# portfolio/settings/dev.py
from .base import *

DEBUG = True

ALLOWED_HOSTS = ["*"]

DATABASES["default"] = DATABASES["development"]
CACHES["default"] = CACHES["development"]

INSTALLED_APPS += ["debug_toolbar"]

MIDDLEWARE.insert(0, "debug_toolbar.middleware.DebugToolbarMiddleware")

INTERNAL_IPS = ["127.0.0.1"]

print("🚀 Running in DEVELOPMENT mode")
