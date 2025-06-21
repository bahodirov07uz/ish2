
from pathlib import Path
import os

BASE_DIR = Path(__file__).resolve().parent.parent


SECRET_KEY = 'django-insecure-*inyq5sw68&no_3*1q@(1vf%q=^^xah2kr(q!bs_j2u$*l26_q'

DEBUG = True

ALLOWED_HOSTS = ['localhost', '127.0.0.1', 'ish2.onrender.com']

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.humanize',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'main.apps.MainConfig',
    'shop.apps.ShopConfig',
    'xomashyo.apps.XomashyoConfig',
    'autentific.apps.AutentificConfig',
    'user_app.apps.UserAppConfig',
    'corsheaders',
    'rest_framework',

]

AUTH_USER_MODEL = 'main.CustomUser'

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",  
    "django.middleware.common.CommonMiddleware",
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'main.middlewares.VisitorTrackingMiddleware',
]
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",  # Frontend domeni (React, Vue yoki boshqa)
    "http://127.0.0.1:8000",
]

CORS_ALLOW_ALL_ORIGINS = True

CSRF_TRUSTED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:8000",
    'https://e721-213-230-114-217.ngrok-free.app'
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
                "shop.context_pros.cart_items",
                "shop.context_pros.category_items",
                'shop.context_pros.categories_processor',
                'shop.context_pros.product_filter',
                'shop.context_pros.avg_rating',

            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'


# Database
# https://docs.djangoproject.com/en/5.1/ref/settings/#databases
import dj_database_url

DATABASES = {
    'default': dj_database_url.config(
        default='postgresql://crm_user:X3UT340yLKbC8X9rNFKTQ7kkoNi18ebd@dpg-d1b7gc6uk2gs739el1n0-a.oregon-postgres.render.com/crm_db_yw2e',
        conn_max_age=600,
        ssl_require=True
    )
}


LOGIN_REDIRECT_URL = '/'
LOGIN_URL = '/login/'
LOGOUT_REDIRECT_URL = 'login_page'


# Password validation
# https://docs.djangoproject.com/en/5.1/ref/settings/#auth-password-validators

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

# settings.py



# Internationalization
# https://docs.djangoproject.com/en/5.1/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.1/howto/static-files/
STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'staticfiles']  # Bu dev modeda ishlaydi

STATIC_ROOT = BASE_DIR / 'static'  # collectstatic uchun bu joy




# MEDIA_URL = '/media/'
# MEDIA_ROOT = BASE_DIR / 'media'

# Default primary key field type
# https://docs.djangoproject.com/en/5.1/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / "media"
