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
ENV = os.getenv("DJANGO_ENV", "dev")  # 'dev' or 'prod'
IS_PROD = ENV == "prod"

# Load .env file
env_file = BASE_DIR / (".env.prod" if IS_PROD else ".env.dev")
load_dotenv(dotenv_path=env_file)

# ----------------------------
# SECURITY
# ----------------------------
SECRET_KEY = os.getenv("PROJECT_KEY")
if IS_PROD and not SECRET_KEY:
    raise ImproperlyConfigured("PROJECT_KEY must be set in production")

DEBUG = not IS_PROD

ALLOWED_HOSTS = (
    [h.strip() for h in os.getenv("ALLOWED_HOSTS", "").split(",") if h.strip()]
    if IS_PROD
    else ["localhost", "127.0.0.1"]
)

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
    "django_browser_reload",
    "widget_tweaks",
    "storages",
    "allauth",
    "allauth.account",
]

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
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "allauth.account.middleware.AccountMiddleware",
]

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
LOGIN_REDIRECT_URL = "/"
LOGOUT_REDIRECT_URL = "/accounts/login/"
ACCOUNT_LOGIN_METHODS = {"email", "username"}
ACCOUNT_SIGNUP_FIELDS = ["email*", "password1*", "password2*"]
# ACCOUNT_EMAIL_VERIFICATION = "mandatory"
ACCOUNT_LOGIN_ON_EMAIL_CONFIRMATION = True
ACCOUNT_LOGOUT_ON_PASSWORD_CHANGE = True

# ----------------------------
# DATABASE
# ----------------------------
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

# Dev vs Prod storage
if IS_PROD:
    # AWS / Backblaze B2
    AWS_ACCESS_KEY_ID = os.getenv("B2_APP_KEY_ID")
    AWS_SECRET_ACCESS_KEY = os.getenv("B2_APP_KEY")
    AWS_STORAGE_BUCKET_NAME = os.getenv("B2_BUCKET_NAME")
    AWS_S3_REGION_NAME = "us-east-005"
    AWS_S3_ENDPOINT_URL = f"https://s3.{AWS_S3_REGION_NAME}.backblazeb2.com"

    STORAGES = {
        "default": {
            "BACKEND": "storages.backends.s3boto3.S3Boto3Storage",
            "OPTIONS": {"default_acl": None, "file_overwrite": False},
        },
        "staticfiles": {
            "BACKEND": "storages.backends.s3boto3.S3Boto3Storage",
        },
    }

    MEDIA_URL = f"{AWS_S3_ENDPOINT_URL}/{AWS_STORAGE_BUCKET_NAME}/"

else:
    # Local filesystem
    STATICFILES_DIRS = [BASE_DIR / "static"]
    STATIC_ROOT = BASE_DIR / "staticfiles"

    MEDIA_URL = "/media/"
    MEDIA_ROOT = BASE_DIR / "media"

# ----------------------------
# EMAIL
# ----------------------------
DEFAULT_FROM_EMAIL = "Centralize GIS <no-reply@centralizegis.com>"

if IS_PROD:
    EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
    # EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
    # EMAIL_HOST = os.getenv("EMAIL_HOST")
    # EMAIL_PORT = int(os.getenv("EMAIL_PORT", 587))
    # EMAIL_USE_TLS = True
    # EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER")
    # EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD")
else:
    EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# ----------------------------
# TAILWIND
# ----------------------------
TAILWIND_APP_NAME = "theme"

# ----------------------------
# DEFAULT AUTO FIELD
# ----------------------------
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
