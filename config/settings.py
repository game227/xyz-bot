"""Django settings for xyz-bot.

Standalone project — no relation to the original xyz Django project or
its database. Own DB, own code. The Telegram bot (apps.bot) is the only
user interface — content management, staff role assignment, subscriptions,
live sessions and support are all handled inside the bot. Django's default
/admin/ stays wired up only as a technical fallback (not a designed UI).
"""
import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / '.env')


def env_bool(key, default=False):
    value = os.getenv(key)
    if value is None:
        return default
    return value.strip().lower() in ('1', 'true', 'yes', 'on')


# =========================================================
# CORE
# =========================================================
SECRET_KEY = os.getenv('SECRET_KEY', 'insecure-dev-key-change-me')
DEBUG = env_bool('DEBUG', True)
ALLOWED_HOSTS = [h.strip() for h in os.getenv('ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',') if h.strip()]

# =========================================================
# APPLICATIONS
# =========================================================
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    'apps.core.apps.CoreConfig',
    'apps.accounts.apps.AccountsConfig',
    'apps.education.apps.EducationConfig',
    'apps.exam.apps.ExamConfig',
    'apps.progress.apps.ProgressConfig',
    'apps.subscription.apps.SubscriptionConfig',
    'apps.live.apps.LiveConfig',
    'apps.notifications.apps.NotificationsConfig',
    'apps.bot.apps.BotConfig',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
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

WSGI_APPLICATION = 'config.wsgi.application'

# =========================================================
# DATABASE — SQLite by default (zero setup); set USE_POSTGRES=True + the
# fields below to use Postgres instead (own DB, never the xyz one).
# =========================================================
if env_bool('USE_POSTGRES', False):
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': os.getenv('DB_NAME', 'xyzbot'),
            'USER': os.getenv('DB_USER', 'xyzbot_user'),
            'PASSWORD': os.getenv('DB_PASSWORD', ''),
            'HOST': os.getenv('DB_HOST', 'localhost'),
            'PORT': os.getenv('DB_PORT', '5432'),
            'CONN_MAX_AGE': 60,
        }
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }

# =========================================================
# PASSWORD VALIDATION
# =========================================================
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator', 'OPTIONS': {'min_length': 8}},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
]

# =========================================================
# INTERNATIONALIZATION
# =========================================================
LANGUAGE_CODE = 'uz'
TIME_ZONE = os.getenv('TIME_ZONE', 'Asia/Tashkent')
USE_I18N = True
USE_TZ = True

# =========================================================
# STATIC & MEDIA
# =========================================================
STATIC_URL = 'static/'
STATICFILES_DIRS = [BASE_DIR / 'static'] if (BASE_DIR / 'static').exists() else []
STATIC_ROOT = BASE_DIR / 'staticfiles'

MEDIA_URL = 'media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# =========================================================
# AUTH — web boshqaruv paneli endi yo'q (butunlay botga o'tkazildi); qolgan
# yagona veb interfeys — Django'ning o'zining /admin/'i, faqat zaxira sifatida.
# =========================================================
AUTH_USER_MODEL = 'accounts.CustomUser'
LOGIN_URL = 'admin:login'
LOGIN_REDIRECT_URL = 'admin:index'
LOGOUT_REDIRECT_URL = 'admin:login'

# =========================================================
# LOGGING — konsol + faylga (logs/django.log, logs/bot.log). Xatoliklarni
# keyinchalik tekshirish uchun; bot xatolari qo'shimcha ADMIN_TELEGRAM_IDS'ga
# push qilinadi (apps.bot.bot.dispatcher).
# =========================================================
LOGS_DIR = BASE_DIR / 'logs'
LOGS_DIR.mkdir(exist_ok=True)

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {'verbose': {'format': '[{asctime}] {levelname} {name}: {message}', 'style': '{'}},
    'handlers': {
        'console': {'class': 'logging.StreamHandler', 'formatter': 'verbose'},
        'django_file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': LOGS_DIR / 'django.log',
            'maxBytes': 5 * 1024 * 1024,
            'backupCount': 3,
            'formatter': 'verbose',
        },
        'bot_file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': LOGS_DIR / 'bot.log',
            'maxBytes': 5 * 1024 * 1024,
            'backupCount': 3,
            'formatter': 'verbose',
        },
    },
    'root': {'handlers': ['console', 'django_file'], 'level': 'INFO'},
    'loggers': {
        'bot': {'handlers': ['console', 'bot_file'], 'level': 'INFO', 'propagate': False},
        'live': {'handlers': ['console', 'bot_file'], 'level': 'INFO', 'propagate': False},
        'subscription': {'handlers': ['console', 'bot_file'], 'level': 'INFO', 'propagate': False},
        'notifications': {'handlers': ['console', 'bot_file'], 'level': 'INFO', 'propagate': False},
    },
}

# =========================================================
# TELEGRAM BOT
# =========================================================
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '').strip()
SITE_BASE_URL = os.getenv('SITE_BASE_URL', 'http://localhost:8000').rstrip('/')
TELEGRAM_VIDEO_MAX_MB = int(os.getenv('TELEGRAM_VIDEO_MAX_MB', '45'))

# Web panelga bog'lanmagan holda ham botda "Boshqaruv" menyusiga kira oladigan
# Telegram ID'lar (vergul bilan ajratilgan). `grant_bot_admin` buyrug'i bunday
# odamlarni CustomUser sifatida ham ADMIN qilib qo'yadi — bu ro'yxat shunchaki
# qo'shimcha, kod darajasidagi kafolat.
ADMIN_TELEGRAM_IDS = [
    int(x) for x in os.getenv('ADMIN_TELEGRAM_IDS', '').split(',') if x.strip().isdigit()
]

# Bot ishga tushish rejimi: 'polling' (dev, default) yoki 'webhook' (production,
# ochiq HTTPS manzil talab qiladi).
BOT_MODE = os.getenv('BOT_MODE', 'polling').strip().lower()
WEBHOOK_URL = os.getenv('WEBHOOK_URL', '').rstrip('/')  # masalan https://example.com
WEBHOOK_PATH = os.getenv('WEBHOOK_PATH', '/telegram/webhook/')
WEBHOOK_SECRET = os.getenv('WEBHOOK_SECRET', '').strip()
WEBHOOK_LISTEN_HOST = os.getenv('WEBHOOK_LISTEN_HOST', '0.0.0.0')
WEBHOOK_LISTEN_PORT = int(os.getenv('WEBHOOK_LISTEN_PORT', '8081'))
