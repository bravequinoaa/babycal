from pathlib import Path

import environ

BASE_DIR = Path(__file__).resolve().parent.parent

env = environ.Env(
    DEBUG=(bool, False),
    OTP_PROVIDER_ENABLED=(bool, False),
    OTP_CODE_TTL_SECONDS=(int, 300),
    SESSION_COOKIE_AGE=(int, 60 * 60 * 24 * 365),
)
environ.Env.read_env(BASE_DIR / ".env")

SECRET_KEY = env("SECRET_KEY", default="insecure-dev-key-change-me")
DEBUG = env("DEBUG")
ALLOWED_HOSTS = env.list("ALLOWED_HOSTS", default=["localhost", "127.0.0.1"])

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django_ckeditor_5",
    "accounts",
    "schedules",
    "helppage",
    "adminparents",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "babycal.middleware.RequestLoggingMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "babycal.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "babycal.wsgi.application"

DATABASES = {
    "default": env.db(
        "DATABASE_URL",
        default=f"sqlite:///{BASE_DIR / 'db.sqlite3'}",
    )
}

AUTH_USER_MODEL = "accounts.User"

AUTHENTICATION_BACKENDS = [
    "accounts.backends.PhoneOTPBackend",
    # Kept for /django-admin/ superuser password login (see accounts.models.UserManager.create_superuser).
    "django.contrib.auth.backends.ModelBackend",
]

AUTH_PASSWORD_VALIDATORS = []

LANGUAGE_CODE = "en-us"
TIME_ZONE = env("TIME_ZONE", default="America/New_York")
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static"]
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    # Plain (non-manifest) storage: avoids requiring `collectstatic` to have
    # already run just to render a page (e.g. in tests or a fresh dev checkout).
    # Whitenoise's middleware still serves these efficiently with cache headers.
    "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
}

MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

LOGIN_URL = "accounts:login"
LOGIN_REDIRECT_URL = "schedules:calendar"
LOGOUT_REDIRECT_URL = "accounts:login"

# "Remember me": long-lived session, not expired at browser close.
SESSION_COOKIE_AGE = env("SESSION_COOKIE_AGE")
SESSION_EXPIRE_AT_BROWSER_CLOSE = False
SESSION_SAVE_EVERY_REQUEST = True

# Phone-based login (see accounts app). When disabled, login falls back to
# no-verification (SPEC.md section 3) since no SMS provider is wired up yet.
OTP_PROVIDER_ENABLED = env("OTP_PROVIDER_ENABLED")
OTP_CODE_TTL_SECONDS = env("OTP_CODE_TTL_SECONDS")

# Twilio (unused stub target — see sms/services.py)
TWILIO_ACCOUNT_SID = env("TWILIO_ACCOUNT_SID", default="")
TWILIO_AUTH_TOKEN = env("TWILIO_AUTH_TOKEN", default="")
TWILIO_FROM_NUMBER = env("TWILIO_FROM_NUMBER", default="")

# Email (parent claim notifications)
EMAIL_BACKEND = env(
    "EMAIL_BACKEND", default="django.core.mail.backends.console.EmailBackend"
)
EMAIL_HOST = env("EMAIL_HOST", default="")
EMAIL_PORT = env.int("EMAIL_PORT", default=587)
EMAIL_HOST_USER = env("EMAIL_HOST_USER", default="")
EMAIL_HOST_PASSWORD = env("EMAIL_HOST_PASSWORD", default="")
EMAIL_USE_TLS = env.bool("EMAIL_USE_TLS", default=True)
DEFAULT_FROM_EMAIL = env("DEFAULT_FROM_EMAIL", default="babycal@example.com")

CKEDITOR_5_CONFIGS = {
    "default": {
        "toolbar": ["bold", "italic", "underline", "|", "bulletedList", "numberedList", "|", "link", "|", "undo", "redo"],
    }
}

LOG_DIR = BASE_DIR / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {"format": "{asctime} {levelname} {name} {message}", "style": "{"},
    },
    "handlers": {
        "console": {"class": "logging.StreamHandler", "formatter": "verbose"},
        "app_file": {
            "class": "logging.handlers.RotatingFileHandler",
            "filename": str(LOG_DIR / "app.log"),
            "maxBytes": 5 * 1024 * 1024,
            "backupCount": 5,
            "formatter": "verbose",
        },
        "request_file": {
            "class": "logging.handlers.RotatingFileHandler",
            "filename": str(LOG_DIR / "requests.log"),
            "maxBytes": 5 * 1024 * 1024,
            "backupCount": 5,
            "formatter": "verbose",
        },
        "django_file": {
            "class": "logging.handlers.RotatingFileHandler",
            "filename": str(LOG_DIR / "django.log"),
            "maxBytes": 5 * 1024 * 1024,
            "backupCount": 5,
            "formatter": "verbose",
        },
    },
    "loggers": {
        # Django's own request/error logging (500s, security warnings, etc.)
        "django": {"handlers": ["console", "django_file"], "level": "INFO", "propagate": False},
        # One line per request: method, path, status, duration, logged-in user.
        "babycal.request": {"handlers": ["console", "request_file"], "level": "INFO", "propagate": False},
        # App-level business events (login/OTP flow, claims, sms/email stubs).
        "accounts": {"handlers": ["console", "app_file"], "level": "INFO", "propagate": False},
        "schedules": {"handlers": ["console", "app_file"], "level": "INFO", "propagate": False},
        "helppage": {"handlers": ["console", "app_file"], "level": "INFO", "propagate": False},
        "adminparents": {"handlers": ["console", "app_file"], "level": "INFO", "propagate": False},
        "sms": {"handlers": ["console", "app_file"], "level": "INFO", "propagate": False},
        "notifications": {"handlers": ["console", "app_file"], "level": "INFO", "propagate": False},
    },
}

if not DEBUG:
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    SESSION_COOKIE_SECURE = env.bool("SESSION_COOKIE_SECURE", default=True)
    CSRF_COOKIE_SECURE = env.bool("CSRF_COOKIE_SECURE", default=True)
