"""
Django settings for interlab project.

Generated by 'django-admin startproject' using Django 3.1.11.

For more information on this file, see
https://docs.djangoproject.com/en/3.1/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/3.1/ref/settings/
"""
from pathlib import Path
import distutils.util
import os  # isort:skip
import sys

# Required for local sqlite migrations
from dotenv import load_dotenv
load_dotenv()

gettext = lambda s: s
DATA_DIR = os.path.dirname(os.path.dirname(__file__))

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# To have GITHUB compatible test reports
TEST_RUNNER = 'xmlrunner.extra.djangotestrunner.XMLTestRunner'
TEST_OUTPUT_DIR = os.path.join(BASE_DIR, 'test')
TEST_OUTPUT_FILE_NAME = 'test-results.xml'

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/3.1/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get('SECRET_KEY')

# SECURITY WARNING: don't run with debug turned on in production!
ENVIRON_DEBUG = os.environ.get('DEBUG')
if ENVIRON_DEBUG != None:
    DEBUG = distutils.util.strtobool(ENVIRON_DEBUG)
else:
    DEBUG = False

ALLOWED_HOSTS = ['*']
CORS_ORIGIN_ALLOW_ALL = True

# Application definition


ROOT_URLCONF = 'interlab.urls'



WSGI_APPLICATION = 'interlab.wsgi.application'


# Database
# https://docs.djangoproject.com/en/3.1/ref/settings/#databases




# Password validation
# https://docs.djangoproject.com/en/3.1/ref/settings/#auth-password-validators

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

# Available password hashers
# https://docs.djangoproject.com/fr/3.1/ref/settings/#std:setting-PASSWORD_HASHERS
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.PBKDF2PasswordHasher',
    'django.contrib.auth.hashers.PBKDF2SHA1PasswordHasher',
    'django.contrib.auth.hashers.Argon2PasswordHasher',
    'django.contrib.auth.hashers.BCryptPasswordHasher', # For Fabmanager user import support.
]


# Internationalization
# https://docs.djangoproject.com/en/3.1/topics/i18n/

LANGUAGE_CODE = 'fr'

TIME_ZONE = 'Europe/Zurich'

USE_I18N = True

USE_L10N = False

USE_TZ = False

LOCALE_PATHS = [
    os.path.join(BASE_DIR, 'locale')
]


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/3.1/howto/static-files/

STATIC_URL = '/static/'
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(DATA_DIR, 'media')
STATIC_ROOT = os.path.join(DATA_DIR, 'static')
STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.ManifestStaticFilesStorage'

STATICFILES_DIRS = (
    os.path.join(BASE_DIR, 'build'),
)
SITE_ID = 1


TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'interlab', 'templates')],
        'OPTIONS': {
            'context_processors': [
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'django.template.context_processors.i18n',
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.template.context_processors.media',
                'django.template.context_processors.csrf',
                'django.template.context_processors.tz',
                'sekizai.context_processors.sekizai',
                'django.template.context_processors.static',
                'cms.context_processors.cms_settings',
                'newsletter.forms.newsletter_context'
            ],
            'loaders': [
                'django.template.loaders.filesystem.Loader',
                'django.template.loaders.app_directories.Loader'
            ],
        },
    },
]


MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'cms.middleware.utils.ApphookReloadMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'oauth2_provider.middleware.OAuth2TokenMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'debug_toolbar.middleware.DebugToolbarMiddleware',
    'cms.middleware.user.CurrentUserMiddleware',
    'cms.middleware.page.CurrentPageMiddleware',
    'cms.middleware.toolbar.ToolbarMiddleware',
    'cms.middleware.language.LanguageCookieMiddleware',
    'django_htmx.middleware.HtmxMiddleware',
]

INSTALLED_APPS = [
    'accounts',
    'djangocms_admin_style',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.admin',
    'django.contrib.sites',
    'django.contrib.sitemaps',
    'django.contrib.staticfiles',
    'django.contrib.messages',
    'oauth2_provider',
    'webpack_loader',
    'cms',
    'menus',
    'sekizai',
    'treebeard',
    'djangocms_text_ckeditor',
    'filer',
    'easy_thumbnails',
    'djangocms_bootstrap4',
    'djangocms_bootstrap4.contrib.bootstrap4_alerts',
    'djangocms_bootstrap4.contrib.bootstrap4_badge',
    'djangocms_bootstrap4.contrib.bootstrap4_card',
    'djangocms_bootstrap4.contrib.bootstrap4_carousel',
    'djangocms_bootstrap4.contrib.bootstrap4_collapse',
    'djangocms_bootstrap4.contrib.bootstrap4_content',
    'djangocms_bootstrap4.contrib.bootstrap4_grid',
    'djangocms_bootstrap4.contrib.bootstrap4_jumbotron',
    'djangocms_bootstrap4.contrib.bootstrap4_link',
    'djangocms_bootstrap4.contrib.bootstrap4_listgroup',
    'djangocms_bootstrap4.contrib.bootstrap4_media',
    'djangocms_bootstrap4.contrib.bootstrap4_picture',
    'djangocms_bootstrap4.contrib.bootstrap4_tabs',
    'djangocms_bootstrap4.contrib.bootstrap4_utilities',
    'djangocms_file',
    'djangocms_icon',
    'djangocms_link',
    'djangocms_picture',
    'djangocms_style',
    'djangocms_video',
    'django_registration',
    'crispy_forms',
    'crispy_bootstrap5',
    'fabcal.apps.FabcalConfig',
    'debug_toolbar',
    'organizations',
    'newsletter.apps.NewsletterConfig',
    'machines',
    'mathfilters',
    'openings',
    'colorfield',
    'django_filters',
    'url_or_relative_url_field',
    'django_q',
    'django_db_logger',
    'share',
    'django_htmx',
    'analytical',
    'phonenumber_field',
    'payments.apps.PaymentsConfig',
    'interlab',
    'api.apps.APIConfig',
    'rest_framework',
    'rest_framework.authtoken',
]

LANGUAGES = (
    ## Customize this
    ('fr', gettext('fr')),
)


Q_CLUSTER = {
    'name': 'DjangORM',
    'workers': 1,
    'timeout': 90,
    'retry': 120,
    'queue_limit': 50,
    'bulk': 10,
    'orm': 'default'
}

CMS_LANGUAGES = {
    ## Customize this
    1: [
        {
            'code': 'fr',
            'name': gettext('fr'),
            'redirect_on_fallback': True,
            'public': True,
            'hide_untranslated': False,
        },
    ],
    'default': {
        'redirect_on_fallback': True,
        'public': True,
        'hide_untranslated': False,
    },
}

CMS_TEMPLATES = (
    ## Customize this
    ('page.html', 'Page'),
    ('feature.html', 'Page with Feature')
)

X_FRAME_OPTIONS = 'SAMEORIGIN'

CMS_PERMISSION = True

CMS_PLACEHOLDER_CONF = {}

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


if any(item == 'test' for item in sys.argv):
    # Test if run test or on local computer
    DATABASES = {
        'default' : {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': os.path.join(BASE_DIR, 'test', 'tests.sqlite3'),
        }
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': os.environ.get('POSTGRES_NAME'),
            'USER': os.environ.get('POSTGRES_USER'),
            'PASSWORD': os.environ.get('POSTGRES_PASSWORD'),
            'HOST': os.environ.get('POSTGRES_HOST'),
            'PORT': os.environ.get('POSTGRES_PORT')
        }
    }

DEFAULT_FROM_EMAIL=os.environ.get('DEFAULT_FROM_EMAIL')
EMAIL_HOST=os.environ.get('EMAIL_HOST')
EMAIL_PORT=os.environ.get('EMAIL_PORT')
EMAIL_HOST_USER=os.environ.get('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD=os.environ.get('EMAIL_HOST_PASSWORD')
EMAIL_SUBJECT_PREFIX=os.environ.get('EMAIL_SUBJECT_PREFIX')
EMAIL_USE_TLS=os.environ.get('EMAIL_USE_TLS')


THUMBNAIL_PROCESSORS = (
    'easy_thumbnails.processors.colorspace',
    'easy_thumbnails.processors.autocrop',
    'filer.thumbnail_processors.scale_and_crop_with_subject_location',
)

# User registration
ACCOUNT_ACTIVATION_DAYS = 7 # One-week activation window

OAUTH2_PROVIDER = {
    "OIDC_ENABLED": True,
    "SCOPES": {
        "openid": "OpenID Connect scope",
        # ... any other scopes that you use
    },
    "OAUTH2_VALIDATOR_CLASS": "interlab.oauth_validator.CustomOAuth2Validator",
    # ... any other settings you want
}

STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
)
 
COMPRESS_PRECOMPILERS = (
    ('text/x-scss', 'django_libsass.SassCompiler'),
)

WEBPACK_LOADER = {
    'DEFAULT': {
        'STATS_FILE': str(BASE_DIR / 'build' / 'webpack-stats.json'),
    },
}

# Crispy form
CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap5"
CRISPY_TEMPLATE_PACK = "bootstrap5"

#django-debug-toolbar
if DEBUG:
    import os  # only if you haven't already imported this
    import socket  # only if you haven't already imported this
    hostname, _, ips = socket.gethostbyname_ex(socket.gethostname())
    INTERNAL_IPS = [ip[:-1] + '1' for ip in ips] + ['127.0.0.1', '10.0.2.2']

# django-organizations
INVITATION_BACKEND = 'accounts.backends.CustomInvitationsBackend'

# Logout redirection
LOGOUT_REDIRECT_URL = '/'

# This is required to have correct protocol on links generated
# PLEASE READ WARNING INFO:
#  * https://docs.djangoproject.com/en/1.10/ref/settings/#std:setting-SECURE_PROXY_SSL_HEADER
if DEBUG == False:
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    SECURE_SSL_REDIRECT = True

# Login with email
AUTH_USER_MODEL = 'accounts.CustomUser'
AUTHENTICATION_BACKENDS = ['accounts.backends.EmailBackend']

# --- CKEDITOR STYLE MANAGEMENT AND ADDITIONNAL CONTENT ---

# Allow adding iframe to CMS ckeditor for video integration
TEXT_ADDITIONAL_TAGS = ('iframe',)
TEXT_ADDITIONAL_ATTRIBUTES = ('allow', 'allowfullscreen', 'frameborder', 'height', 'src', 'title', 'width', 'name',)

class WebpackCssFilesAccessor(list):
    """This class provide lazy initialization for CKEditor webpacked settings file"""
    def __iter__(self):
        import webpack_loader.utils # Will fail if invoke on settings initialization
        return [p['url'] for p in webpack_loader.utils.get_files('app', 'css')].__iter__()

CKEDITOR_SETTINGS = {
    'language': '{{ language }}',
    'contentsCss': WebpackCssFilesAccessor(), # Let CKEditor use webpacked styles sheets
    'extraAllowedContent': 'iframe[*]'
}

# ---

# UserReport
USERREPORT_LINK = os.environ.get('USERREPORT_LINK')
USERREPORT_TOKEN = os.environ.get('USERREPORT_TOKEN')

# FabCal
FABCAL_MINIMUM_RESERVATION_TIME = 30
FABCAL_RESERVATION_INCREMENT_TIME = 30

# Logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'filters': {
    'require_debug_false': {
        '()': 'django.utils.log.RequireDebugFalse',
        },
    },
    'handlers': {
        'db_log': {
            'level': 'DEBUG',
            'class': 'django_db_logger.db_log_handler.DatabaseLogHandler',
            'filters': ['require_debug_false'], # only records error in DB when DEBUG is False

        },
    },
    'loggers': {
        'db': {
            'handlers': ['db_log'],
            'level': 'DEBUG'
        },
        'django.request': { # logging 500 errors to database
            'handlers': ['db_log'],
            'level': 'ERROR',
            'propagate': False,
        }
    }
}


# Matomo
MATOMO_DOMAIN_PATH = os.environ.get('MATOMO_DOMAIN_PATH')
MATOMO_SITE_ID = os.environ.get('MATOMO_SITE_ID')

# STRIPE
STRIPE_PUBLIC_KEY = os.environ.get('STRIPE_PUBLIC_KEY')
STRIPE_SECRET_KEY = os.environ.get('STRIPE_SECRET_KEY')
STRIPE_WEBHOOK_SECRET = os.environ.get('STRIPE_WEBHOOK_SECRET')
STRIPE_CURRENCY = os.environ.get('STRIPE_CURRENCY')

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': 'rest_framework.authentication.TokenAuthentication',
    'DEFAULT_VERSIONING_CLASS': 'rest_framework.versioning.URLPathVersioning'
}