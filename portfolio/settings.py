"""
Django settings for portfolio project.

Generated by 'django-admin startproject' using Django 4.2.17.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/4.2/ref/settings/
"""

from pathlib import Path
from decouple import config
from django.utils.translation import gettext_lazy as _
import os

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/4.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = config('APP_SECRET')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

ALLOWED_HOSTS = ['localhost', 'mohammadasdjangodev.pythonanywhere.com']

INTERNAL_IPS = [
    "127.0.0.1",
]

# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'debug_toolbar',
    'crispy_forms',
    'core.apps.CoreConfig',
    'projects.apps.ProjectsConfig',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'debug_toolbar.middleware.DebugToolbarMiddleware',
]

ROOT_URLCONF = 'portfolio.urls'


TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            Path.joinpath(BASE_DIR , "templates"),
        ],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'portfolio.wsgi.application'

# Database
# https://docs.djangoproject.com/en/4.2/ref/settings/#databases

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.mysql",
        "NAME": config("MYSQL_DB_NAME"),
        "USER" : config("MYSQL_DB_USER"),
        "HOST" : config("MYSQL_DB_HOST"),
        "PASSWORD" : config("MYSQL_DB_PASS"),
        'OPTIONS': {
            'sql_mode': 'traditional',
            'charset': 'utf8mb4',
        }
    },
    'development': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': 'portfolio_db',
    }
}

# Cache
# https://docs.djangoproject.com/en/5.1/topics/cache/

servers = config("MEMCACHED_SERVERS")
username = config("MEMCAHCED_USERNAME")
password = config("MEMCACHED_PASSWORD")

CACHES = {
    'default' : {
        'BACKEND': 'django_bmemcached.memcached.BMemcached',
        'LOCATION' : servers,
        'TIMEOUT' : None,
        'OPTIONS' : {
            'username' : username,
            'password' : password
        }
    },
    'development': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'unique-snowflake',  # A unique identifier for the cache
    }
}

# Password validation
# https://docs.djangoproject.com/en/4.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/4.2/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.2/howto/static-files/

STATIC_URL = 'static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')  # Directory to collect static files
STATICFILES_DIRS = [
    BASE_DIR / 'static/'
]
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'


# Crispy forms 
# https://django-crispy-forms.readthedocs.io/en/latest/
CRISPY_TEMPLATE_PACK = 'tailwind'

# Default primary key field type
# https://docs.djangoproject.com/en/4.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Translation and Localization
# https://docs.djangoproject.com/en/5.1/topics/i18n/translation/
LANGUAGE_CODE = 'en'

USE_I18N = True
USE_L10N = True

# Available languages (English + Japanese)
LANGUAGES = [
    ("en", _("English")),
    ("ja", _("Japanese")),
]

LANG_COOKIE_NAME = "django_language"
LANG_COOKIE_AGE = 31536000  # One Year

LOCALE_PATHS = [
    BASE_DIR / "locale"
]

# Github API URL
GITHUB_API = config("GITHUB_API")
GITHUB_API_TOKEN = config("GITHUB_TOKEN")

# Leetcode Account
LEETCODE_GRAPHQL_API = config("LEETCODE_GRAPHQL_API")
LEETCODE_USERNAME = config("LEETCODE_USERNAME")
LEETCODE_REST_API = config("LEETCODE_REST_API")