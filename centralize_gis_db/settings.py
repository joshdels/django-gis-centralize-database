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

DEBUG = not IS_PROD

WINDOWS = os.getenv("WINDOWS")

# ----------------------------
# SECURITY
# ----------------------------
SECRET_KEY = os.getenv("PROJECT_KEY")

if IS_PROD and not SECRET_KEY:
    raise ImproperlyConfigured("PROJECT_KEY must be set in production")

if IS_PROD:
    CSRF_TRUSTED_ORIGINS = [
        "https://topmapsolutions.com",
        "https://www.topmapsolutions.com",
    ]
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = 3600
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True


if IS_PROD:
    ALLOWED_HOSTS = [
        "topmapsolutions.com",
        "www.topmapsolutions.com",
    ]
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
    "rest_framework.authtoken",
    "widget_tweaks",
    "allauth",
    "allauth.account",
    "drf_spectacular",
]

if IS_PROD:
    THIRD_PARTY_APPS += [
        "storages",
    ]

LOCAL_APPS = [
    "gis_database",
    "accounts",
    "api",
    "customer_service",
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

if DEBUG:
    INSTALLED_APPS += ["tailwind", "django_browser_reload", "theme"]

SITE_ID = 1

# ----------------------------
# MIDDLEWARE
# ----------------------------
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
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

if DEBUG:
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
TIME_ZONE = "Asia/Manila"
USE_I18N = True
USE_TZ = True

# ----------------------------
# STATIC & MEDIA
# ----------------------------
STATIC_URL = "/static/"
MEDIA_URL = "/media/"

STATIC_ROOT = BASE_DIR / "staticfiles"

STATICFILES_DIRS = [
    BASE_DIR / "static",
]

MEDIA_ROOT = BASE_DIR / "media"

if IS_PROD:
    # AWS / Backblaze B2

    AWS_ACCESS_KEY_ID = os.getenv("B2_APP_KEY_ID")
    AWS_SECRET_ACCESS_KEY = os.getenv("B2_APP_KEY")
    AWS_STORAGE_BUCKET_NAME = os.getenv("B2_BUCKET_NAME")
    AWS_S3_REGION_NAME = "us-east-005"
    AWS_S3_ENDPOINT_URL = f"https://s3.{AWS_S3_REGION_NAME}.backblazeb2.com"

    # Update these URLs
    MEDIA_URL = f"{AWS_S3_ENDPOINT_URL}/{AWS_STORAGE_BUCKET_NAME}/media/"
    STATIC_URL = f"{AWS_S3_ENDPOINT_URL}/{AWS_STORAGE_BUCKET_NAME}/static/"

    STORAGES = {
        "default": {
            "BACKEND": "storages.backends.s3boto3.S3Boto3Storage",
            "OPTIONS": {
                "default_acl": None,
                "file_overwrite": True,
                "location": "media",
            },
        },
        "staticfiles": {
            "BACKEND": "storages.backends.s3boto3.S3Boto3Storage",
            "OPTIONS": {
                "default_acl": None,
                "file_overwrite": True,
                "location": "static",
            },
        },
    }

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
if not IS_PROD:
    TAILWIND_APP_NAME = "theme"

# THIS IS FOR WINDOWS SETUP
if not IS_PROD:
    if WINDOWS:
        NPM_BIN_PATH = r"C:\nvm4w\nodejs\npm.cmd"
    else:
        NPM_BIN_PATH = "/usr/local/bin/npm"


# ----------------------------
# DEFAULT AUTO FIELD
# ----------------------------
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


# -----------------------------
# DJANGO REST FRAMEWORK API
# ------------------------------

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.TokenAuthentication",
        "rest_framework.authentication.SessionAuthentication",
        "rest_framework.authentication.BasicAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    "DEFAULT_THROTTLE_CLASSES": [
        "rest_framework.throttling.UserRateThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {
        "user": "20/min",
    },
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
}


# ----------------------------
# LOGGING (Add this to the end)
# ----------------------------
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "{levelname} {asctime} {module} {process:d} {thread:d} {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "DEBUG",
    },
    "loggers": {
        "django": {
            "handlers": ["console"],
            "level": "ERROR",
            "propagate": True,
        },
    },
}
