"""
Django settings for techmarket_project project.
"""

import os
import stat
import warnings
from pathlib import Path
from datetime import timedelta

from django.core.exceptions import ImproperlyConfigured

BASE_DIR = Path(__file__).resolve().parent.parent



def _load_dotenv(path):
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8-sig").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        if f"{key}_FILE" in os.environ:
            continue  # the secret is provisioned as a file (e.g. by Vault Agent); .env must not override it
        os.environ.setdefault(key, value.strip().strip('"').strip("'"))


_load_dotenv(BASE_DIR / ".env")

def env(name, default=None, required=False):
    """Read configuration from environment variables (never from source code)."""
    value = os.environ.get(name, default)
    if required and not value:
        raise ImproperlyConfigured(f"Environment variable {name} is required")
    return value


def secret(name, required=False):
    """Read a secret from a file (NAME_FILE) or from an environment variable (NAME).

    File provisioning is preferred: the value never appears in the process environment,
    so it cannot leak through /proc/<pid>/environ, crash dumps or child processes.
    """
    file_path = os.environ.get(f"{name}_FILE")
    if file_path and os.environ.get(name):
        raise ImproperlyConfigured(f"Set either {name} or {name}_FILE, not both")
    if file_path:
        path = Path(file_path)
        try:
            value = path.read_text(encoding="utf-8").strip()
            mode = path.stat().st_mode
        except OSError as exc:
            raise ImproperlyConfigured(f"Cannot read secret file {name}_FILE") from exc
        if os.name == "posix" and mode & (stat.S_IRWXG | stat.S_IRWXO):
            warnings.warn(f"{name}_FILE is readable by group/others, use chmod 600", stacklevel=2)
    else:
        value = os.environ.get(name)
    if required and not value:
        raise ImproperlyConfigured(f"Secret {name} (or {name}_FILE) is required")
    return value


def env_list(name, default=""):
    return [item.strip() for item in env(name, default).split(",") if item.strip()]


# Secure defaults: DEBUG is off unless explicitly enabled, and the app refuses
# to start without a SECRET_KEY instead of falling back to a hardcoded one.
DEBUG = env("DJANGO_DEBUG", "False").lower() == "true"
SECRET_KEY = secret("DJANGO_SECRET_KEY", required=True)
ALLOWED_HOSTS = env_list("DJANGO_ALLOWED_HOSTS", "127.0.0.1,localhost")


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'rest_framework.authtoken',
    'corsheaders',
    'shop',
]


MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'techmarket_project.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'shop.context_processors.storefront_context',
            ],
        },
    },
]

WSGI_APPLICATION = 'techmarket_project.wsgi.application'


# Database

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}


# Password validation

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





PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.Argon2PasswordHasher",
    "django.contrib.auth.hashers.PBKDF2PasswordHasher",
    "django.contrib.auth.hashers.PBKDF2SHA1PasswordHasher",
    "django.contrib.auth.hashers.BCryptSHA256PasswordHasher",
    "django.contrib.auth.hashers.ScryptPasswordHasher",
]








# Internationalization

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)

STATIC_URL = 'static/'
STATICFILES_DIRS = []

LOGIN_URL = 'login'
LOGIN_REDIRECT_URL = 'home'
LOGOUT_REDIRECT_URL = 'home'

# Default primary key field type

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


# Django REST Framework
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticatedOrReadOnly',
    ],
}

# CORS (django-cors-headers): explicit allow-list instead of "*" + credentials
CORS_ALLOWED_ORIGINS = env_list("CORS_ALLOWED_ORIGINS", "http://localhost:8000")

SIMPLE_JWT = {
    # Separate key for JWTs, so rotating one key does not silently break the other.
    # Falls back to SECRET_KEY when JWT_SIGNING_KEY is not provisioned.
    "SIGNING_KEY": secret("JWT_SIGNING_KEY") or SECRET_KEY,
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=15),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=1),
}
CORS_ALLOW_CREDENTIALS = True

# Hardening that applies when DEBUG is off (checked by `manage.py check --deploy`)
if not DEBUG:
    SECURE_SSL_REDIRECT = env("DJANGO_SECURE_SSL_REDIRECT", "True").lower() == "true"
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SESSION_COOKIE_HTTPONLY = True
X_FRAME_OPTIONS = "DENY"
