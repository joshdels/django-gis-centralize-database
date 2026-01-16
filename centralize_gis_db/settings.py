"""
Django settings for centralize_gis_db project.
Refactored for clarity, maintainability, and dev/prod separation.
"""

import os
from pathlib import Path
from dotenv import load_dotenv
from django.core.exceptions import ImproperlyConfigured

# ----------------------------
# BASE DIRECTORIES
# ----------------------------
BASE_DIR = Path(__file__).resolve().parent.parent


# ----------------------------
# ENVIRONMENT
# ----------------------------
def load_env():
    env_dev = BASE_DIR / ".env.dev"
    env_prod = BASE_DIR / ".env.prod"

    if env_dev.exists():
        print("--- Loading Environment: DEV ---")
        load_dotenv(env_dev)
    elif env_prod.exists():
        print("--- Loading Environment: PROD ---")
        load_dotenv(env_prod)
    else:
        print("--- No .env files found. Using System Environment Variables ---")


load_env()

env_status = str(os.getenv("DJANGO_ENV", "dev")).strip().lower()
IS_PROD = env_status == "prod"

WINDOWS = os.getenv("WINDOWS", "False").lower() == "true"

# ----------------------------
# SECURITY
# ----------------------------
SECRET_KEY = os.getenv("PROJECT_KEY")
if IS_PROD and not SECRET_KEY:
    raise ImproperlyConfigured("PROJECT_KEY must be set in production")

DEBUG = os.getenv("DEBUG")

raw_hosts = os.getenv("ALLOWED_HOSTS", "localhost,127.0.0.1")

if IS_PROD:
    ALLOWED_HOSTS = [host.strip() for host in raw_hosts.split(",") if host.strip()]
else:
    ALLOWED_HOSTS = ["localhost", "127.0.0.1", "0.0.0.0"]

# ----------------------------
# INSTALLED APPS
# ----------------------------
DJANGO_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.sites",
]

THIRD_PARTY_APPS = [
    "rest_framework",
    "tailwind",
    "widget_tweaks",
    "allauth",
    "allauth.account",
]

if IS_PROD:
    THIRD_PARTY_APPS += ["storages"]

LOCAL_APPS = [
    "gis_database",
    "theme",
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

SITE_ID = 1

# ----------------------------
# MIDDLEWARE
# ----------------------------
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
]

if IS_PROD:
    MIDDLEWARE += [
        "whitenoise.middleware.WhiteNoiseMiddleware",
    ]

MIDDLEWARE += [
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "allauth.account.middleware.AccountMiddleware",
]

if not IS_PROD:
    MIDDLEWARE.append("django_browser_reload.middleware.BrowserReloadMiddleware")


# ----------------------------
# URLS & TEMPLATES
# ----------------------------
ROOT_URLCONF = "centralize_gis_db.urls"
WSGI_APPLICATION = "centralize_gis_db.wsgi.application"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "gis_database" / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

# ----------------------------
# AUTHENTICATION
# ----------------------------
AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.ModelBackend",
    "allauth.account.auth_backends.AuthenticationBackend",
]

# AllAuth settings
LOGIN_REDIRECT_URL = "/dashboard"
LOGOUT_REDIRECT_URL = "/"

# Authentication Method
ACCOUNT_LOGIN_METHODS = {"email", "username"}
ACCOUNT_SIGNUP_FIELDS = ["email*", "password1*", "password2*"]

# Email Verification logic
ACCOUNT_EMAIL_VERIFICATION = "mandatory"
ACCOUNT_CONFIRM_EMAIL_ON_GET = False
ACCOUNT_LOGIN_ON_EMAIL_CONFIRMATION = True

# Session & Security
ACCOUNT_LOGOUT_ON_PASSWORD_CHANGE = True
ACCOUNT_SESSION_REMEMBER = True
ACCOUNT_PREVENT_ENUMERATION = False

# Redirects
ACCOUNT_EMAIL_CONFIRMATION_AUTHENTICATED_REDIRECT_URL = "/dashboard"
ACCOUNT_EMAIL_CONFIRMATION_ANONYMOUS_REDIRECT_URL = "/accounts/login/"

# ----------------------------
# DATABASE
# ----------------------------
if IS_PROD:
    DATABASES = {
        "default": {
            "ENGINE": "django.contrib.gis.db.backends.postgis",
            "NAME": os.getenv("DB_NAME"),
            "USER": os.getenv("DB_USER"),
            "PASSWORD": os.getenv("DB_PASSWORD"),
            "HOST": os.getenv("DB_HOST", "127.0.0.1"),
            "PORT": os.getenv("DB_PORT", "5432"),
            "CONN_MAX_AGE": 600,
        }
    }

else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }

# ----------------------------
# PASSWORD VALIDATION
# ----------------------------
AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"
    },
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# ----------------------------
# INTERNATIONALIZATION
# ----------------------------
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

# ----------------------------
# STATIC & MEDIA
# ----------------------------
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

STATICFILES_DIRS = [
    BASE_DIR / "static",
    BASE_DIR / "theme" / "static",
]


# Dev vs Prod storage
if IS_PROD:
    # AWS / Backblaze B2
    STATIC_ROOT = BASE_DIR / "staticfiles"

    AWS_ACCESS_KEY_ID = os.getenv("B2_APP_KEY_ID")
    AWS_SECRET_ACCESS_KEY = os.getenv("B2_APP_KEY")
    AWS_STORAGE_BUCKET_NAME = os.getenv("B2_BUCKET_NAME")
    AWS_S3_REGION_NAME = "us-east-005"
    AWS_S3_ENDPOINT_URL = f"https://s3.{AWS_S3_REGION_NAME}.backblazeb2.com"

    STORAGES = {
        "default": {
            "BACKEND": "storages.backends.s3boto3.S3Boto3Storage",
            "OPTIONS": {"default_acl": None, "file_overwrite": True},
        },
        "staticfiles": {
            "BACKEND": "whitenoise.storage.CompressedStaticFilesStorage",
        },
    }

    MEDIA_URL = f"{AWS_S3_ENDPOINT_URL}/{AWS_STORAGE_BUCKET_NAME}/"
else:
    # Local filesystem
    MEDIA_URL = "/media/"
    MEDIA_ROOT = BASE_DIR / "media"

# ----------------------------
# EMAIL
# ----------------------------
WEBSITE_EMAIL = os.getenv("WEBSITE_EMAIL")
DEFAULT_FROM_EMAIL = f"TopMapSolution Customer Support <no-reply@{WEBSITE_EMAIL}>"

if IS_PROD:
    EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
    EMAIL_HOST = os.getenv("BREVO_HOST")
    EMAIL_PORT = int(os.getenv("BREVO_PORT", 587))
    EMAIL_USE_TLS = True
    EMAIL_HOST_USER = os.getenv("BREVO_SMTP_LOGIN")
    EMAIL_HOST_PASSWORD = os.getenv("BREVO_SMTP_PASSWORD")
else:
    EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# ----------------------------
# TAILWIND
# ----------------------------
TAILWIND_APP_NAME = "theme"

# THIS IS FOR WINDOWS SETUP
# Get-Command npm => powershell
if WINDOWS:
    NPM_BIN_PATH = r"C:\nvm4w\nodejs\npm.cmd"

if DEBUG:
    INSTALLED_APPS += ["django_browser_reload"]

# ----------------------------
# DEFAULT AUTO FIELD
# ----------------------------
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
