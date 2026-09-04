"""
Django settings for config project.
"""

import os

from datetime import timedelta
from pathlib import Path

import dj_database_url


# ============================================================
# BASE
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent


# ============================================================
# SEGURANÇA
# ============================================================

SECRET_KEY = os.getenv(
    "DJANGO_SECRET_KEY",
    "django-insecure-dev-only-auditkm-local",
)


DEBUG = os.getenv(
    "DEBUG",
    "True",
).lower() == "true"


ALLOWED_HOSTS = [
    "127.0.0.1",
    "localhost",
    "192.168.0.241",
]


render_hostname = os.getenv(
    "RENDER_EXTERNAL_HOSTNAME",
)

if render_hostname:
    ALLOWED_HOSTS.append(
        render_hostname,
    )


extra_hosts = os.getenv(
    "ALLOWED_HOSTS",
)

if extra_hosts:
    ALLOWED_HOSTS.extend(
        [
            host.strip()
            for host in extra_hosts.split(",")
            if host.strip()
        ]
    )


CSRF_TRUSTED_ORIGINS = []

csrf_origins = os.getenv(
    "CSRF_TRUSTED_ORIGINS",
)

if csrf_origins:
    CSRF_TRUSTED_ORIGINS = [
        origin.strip()
        for origin in csrf_origins.split(",")
        if origin.strip()
    ]


SECURE_PROXY_SSL_HEADER = (
    "HTTP_X_FORWARDED_PROTO",
    "https",
)


# ============================================================
# APLICAÇÕES
# ============================================================

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",

    "trips.apps.TripsConfig",

    "rest_framework",

    "accounts.apps.AccountsConfig",
    "vehicles.apps.VehiclesConfig",
]


# ============================================================
# MIDDLEWARE
# ============================================================

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",

    "whitenoise.middleware.WhiteNoiseMiddleware",

    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]


# ============================================================
# URL / WSGI
# ============================================================

ROOT_URLCONF = "config.urls"


WSGI_APPLICATION = "config.wsgi.application"


# ============================================================
# TEMPLATES
# ============================================================

TEMPLATES = [
    {
        "BACKEND":
            "django.template.backends.django.DjangoTemplates",

        "DIRS": [],

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


# ============================================================
# BANCO DE DADOS
# ============================================================

DATABASE_URL = os.getenv(
    "DATABASE_URL",
)


if DATABASE_URL:
    DATABASES = {
        "default":
            dj_database_url.parse(
                DATABASE_URL,
                conn_max_age=600,
                ssl_require=True,
            ),
    }

else:
    DATABASES = {
        "default": {
            "ENGINE":
                "django.db.backends.sqlite3",

            "NAME":
                BASE_DIR /
                "db.sqlite3",
        },
    }


# ============================================================
# PASSWORD VALIDATION
# ============================================================

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME":
            "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },

    {
        "NAME":
            "django.contrib.auth.password_validation.MinimumLengthValidator",
    },

    {
        "NAME":
            "django.contrib.auth.password_validation.CommonPasswordValidator",
    },

    {
        "NAME":
            "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]


# ============================================================
# INTERNACIONALIZAÇÃO
# ============================================================

LANGUAGE_CODE = "pt-br"


TIME_ZONE = "UTC"


USE_I18N = True


USE_TZ = True


# ============================================================
# STATIC
# ============================================================

STATIC_URL = "/static/"


STATIC_ROOT = (
    BASE_DIR /
    "staticfiles"
)


STORAGES = {
    "staticfiles": {
        "BACKEND":
            "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}


# ============================================================
# MEDIA
# ============================================================

MEDIA_URL = "/media/"


MEDIA_ROOT = (
    BASE_DIR /
    "media"
)


# ============================================================
# USER
# ============================================================

AUTH_USER_MODEL = (
    "accounts.User"
)


# ============================================================
# REST FRAMEWORK
# ============================================================

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ],

    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
}


# ============================================================
# JWT
# ============================================================

JWT_AUTH = {
    "JWT_ALLOW_REFRESH":
        True,

    "JWT_EXPIRATION_DELTA":
        timedelta(
            hours=1,
        ),

    "JWT_REFRESH_EXPIRATION_DELTA":
        timedelta(
            days=7,
        ),
}


SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME":
        timedelta(
            minutes=30,
        ),

    "REFRESH_TOKEN_LIFETIME":
        timedelta(
            days=7,
        ),

    "ROTATE_REFRESH_TOKENS":
        True,

    "BLACKLIST_AFTER_ROTATION":
        False,
}


# ============================================================
# SEGURANÇA EM PRODUÇÃO
# ============================================================

if not DEBUG:
    SECURE_SSL_REDIRECT = True

    SESSION_COOKIE_SECURE = True

    CSRF_COOKIE_SECURE = True

    SECURE_HSTS_SECONDS = 3600

    SECURE_HSTS_INCLUDE_SUBDOMAINS = True

    SECURE_HSTS_PRELOAD = False