from pathlib import Path
from datetime import timedelta
import os
from dotenv import load_dotenv

# =========================================================
# BASE DIRECTORY
# =========================================================

BASE_DIR = Path(__file__).resolve().parent.parent

# =========================================================
# LOAD ENV VARIABLES
# =========================================================

load_dotenv(BASE_DIR / ".env")

# =========================================================
# CORE SETTINGS
# =========================================================

SECRET_KEY = os.getenv("SECRET_KEY", "unsafe-secret-key")

DEBUG = os.getenv("DEBUG", "True") == "True"

ALLOWED_HOSTS = os.getenv(
    "ALLOWED_HOSTS",
    "127.0.0.1,localhost"
).split(",")

# =========================================================
# DJANGO APPLICATIONS
# =========================================================

DJANGO_APPS = [

    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
]

# =========================================================
# THIRD PARTY APPLICATIONS
# =========================================================

THIRD_PARTY_APPS = [

    # REST API
    'rest_framework',
    'rest_framework_simplejwt',
    'rest_framework_simplejwt.token_blacklist',

    # Filtering
    'django_filters',

    # CORS
    'corsheaders',

    # WebSockets
    'channels',

    # Celery
    'django_celery_results',
]

# =========================================================
# LOCAL APPLICATIONS
# =========================================================

LOCAL_APPS = [

    'accounts',
    'riders',
    'contacts',
    'verification',
    'location',
    'announcements',
    'notifications',
    'adminpanel',
    'analytics',
    'security',
    'stages',
    'fines',
    'tracking',
]

# =========================================================
# INSTALLED APPS
# =========================================================

INSTALLED_APPS = (
    DJANGO_APPS
    + THIRD_PARTY_APPS
    + LOCAL_APPS
)

# =========================================================
# MIDDLEWARE
# =========================================================

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

# =========================================================
# URLS / APPLICATION
# =========================================================

ROOT_URLCONF = 'config.urls'

WSGI_APPLICATION = 'config.wsgi.application'

ASGI_APPLICATION = 'config.asgi.application'

# =========================================================
# TEMPLATES
# =========================================================

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',

        'DIRS': [],

        'APP_DIRS': True,

        'OPTIONS': {

            'context_processors': [

                'django.template.context_processors.request',

                'django.contrib.auth.context_processors.auth',

                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

# =========================================================
# DATABASE
# =========================================================

DATABASES = {

    'default': {

        'ENGINE': 'django.db.backends.postgresql',

        'NAME': os.getenv('DB_NAME'),

        'USER': os.getenv('DB_USER'),

        'PASSWORD': os.getenv('DB_PASSWORD'),

        'HOST': os.getenv('DB_HOST', 'localhost'),

        'PORT': os.getenv('DB_PORT', '5432'),

        # DATABASE OPTIMIZATION
        'CONN_MAX_AGE': 60,

        'ATOMIC_REQUESTS': True,
    }
}

# =========================================================
# CUSTOM USER MODEL
# =========================================================

AUTH_USER_MODEL = 'accounts.User'

# =========================================================
# PASSWORD VALIDATORS
# =========================================================

AUTH_PASSWORD_VALIDATORS = [

    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },

    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',

        'OPTIONS': {
            'min_length': 8,
        },
    },

    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },

    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# =========================================================
# DJANGO REST FRAMEWORK
# =========================================================

REST_FRAMEWORK = {

    # AUTHENTICATION
    'DEFAULT_AUTHENTICATION_CLASSES': (

        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),

    # PERMISSIONS
    'DEFAULT_PERMISSION_CLASSES': (

        'rest_framework.permissions.IsAuthenticated',
    ),

    # FILTERING
    'DEFAULT_FILTER_BACKENDS': [

        'django_filters.rest_framework.DjangoFilterBackend',

        'rest_framework.filters.SearchFilter',

        'rest_framework.filters.OrderingFilter',
    ],

    # PAGINATION
    'DEFAULT_PAGINATION_CLASS':

        'rest_framework.pagination.PageNumberPagination',

    'PAGE_SIZE': 20,

    # THROTTLING
    'DEFAULT_THROTTLE_CLASSES': [

        'rest_framework.throttling.AnonRateThrottle',

        'rest_framework.throttling.UserRateThrottle',
    ],

    'DEFAULT_THROTTLE_RATES': {

        'anon': '100/day',

        'user': '1000/day',
    }
}

# =========================================================
# JWT SETTINGS
# =========================================================

SIMPLE_JWT = {

    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=30),

    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),

    'ROTATE_REFRESH_TOKENS': True,

    'BLACKLIST_AFTER_ROTATION': True,

    'UPDATE_LAST_LOGIN': True,

    'AUTH_HEADER_TYPES': ('Bearer',),
}

# =========================================================
# CORS SETTINGS
# =========================================================

CORS_ALLOW_ALL_ORIGINS = DEBUG

CORS_ALLOWED_ORIGINS = [

    "http://localhost:3000",

    "http://127.0.0.1:3000",
]

# =========================================================
# CHANNELS (WEBSOCKETS)
# =========================================================

REDIS_HOST = os.getenv("REDIS_HOST", "127.0.0.1")

REDIS_PORT = os.getenv("REDIS_PORT", "6379")

CHANNEL_LAYERS = {

    'default': {

        'BACKEND': 'channels_redis.core.RedisChannelLayer',

        'CONFIG': {

            'hosts': [(REDIS_HOST, int(REDIS_PORT))],
        },
    },
}

# =========================================================
# CELERY CONFIGURATION
# =========================================================

CELERY_BROKER_URL = f"redis://{REDIS_HOST}:{REDIS_PORT}/0"

CELERY_RESULT_BACKEND = 'django-db'

CELERY_ACCEPT_CONTENT = ['json']

CELERY_TASK_SERIALIZER = 'json'

CELERY_RESULT_SERIALIZER = 'json'

CELERY_TIMEZONE = 'Africa/Kampala'

# =========================================================
# REDIS CACHE
# =========================================================

CACHES = {

    "default": {

        "BACKEND": "django.core.cache.backends.redis.RedisCache",

        "LOCATION": f"redis://{REDIS_HOST}:{REDIS_PORT}/1",
    }
}

# =========================================================
# INTERNATIONALIZATION
# =========================================================

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'Africa/Kampala'

USE_I18N = True

USE_TZ = True

# =========================================================
# STATIC FILES
# =========================================================

STATIC_URL = '/static/'

STATIC_ROOT = BASE_DIR / 'staticfiles'

# =========================================================
# MEDIA FILES
# =========================================================

MEDIA_URL = '/media/'

MEDIA_ROOT = BASE_DIR / 'media'

# =========================================================
# DEFAULT PRIMARY KEY
# =========================================================

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# =========================================================
# LOGGING
# =========================================================

LOGGING = {

    'version': 1,

    'disable_existing_loggers': False,

    'formatters': {

        'verbose': {

            'format': '{levelname} {asctime} {module} {message}',

            'style': '{',
        },
    },

    'handlers': {

        'console': {

            'class': 'logging.StreamHandler',

            'formatter': 'verbose',
        },
    },

    'root': {

        'handlers': ['console'],

        'level': 'INFO',
    },
}

# =========================================================
# SECURITY SETTINGS
# =========================================================

SESSION_COOKIE_SECURE = False

CSRF_COOKIE_SECURE = False

SECURE_BROWSER_XSS_FILTER = True

SECURE_CONTENT_TYPE_NOSNIFF = True

X_FRAME_OPTIONS = 'DENY'

# =========================================================
# PRODUCTION ONLY
# =========================================================

# SECURE_SSL_REDIRECT = True
# SESSION_COOKIE_SECURE = True
# CSRF_COOKIE_SECURE = True

# =========================================================
# ELASTICSEARCH
# =========================================================

ELASTICSEARCH_DSL = {

    'default': {

        'hosts': 'localhost:9200',
    },
}