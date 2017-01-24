"""
Django settings for osmaxx project.

For more information on this file, see
https://docs.djangoproject.com/en/1.10/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.10/ref/settings/
"""
# flake8: noqa
import os
from datetime import timedelta
import environ
from copy import deepcopy

from django.contrib.messages import constants as message_constants
from django.utils import timezone

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(__file__))
ROOT_DIR = environ.Path(__file__) - 3  # (/a/b/myfile.py - 3 = /)
APPS_DIR = ROOT_DIR.path('osmaxx')

env = environ.Env()

# APP CONFIGURATION
# ------------------------------------------------------------------------------
DJANGO_APPS = (
    # Default Django apps:
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Useful template tags:
    'django.contrib.humanize',

    # Admin
    'django.contrib.admin',
    'django.contrib.gis',
)
THIRD_PARTY_APPS = (
    'social_django',
    # messages for users
    'stored_messages',
    # better forms
    'crispy_forms',
    # rest API Framework
    'rest_framework',
    'rest_framework_gis',
    # async execution worker
    'django_rq',
)
# Apps specific for this project go here.
LOCAL_APPS = (
    'osmaxx.version',

    'osmaxx.conversion_api',
    'osmaxx.excerptexport',
    'osmaxx.job_progress',
    'osmaxx.profile',
    'osmaxx.core',
)

# See: https://docs.djangoproject.com/en/dev/ref/settings/#installed-apps
INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

# MIDDLEWARE CONFIGURATION
# ------------------------------------------------------------------------------
MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.auth.middleware.SessionAuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'osmaxx.job_progress.middleware.ExportUpdaterMiddleware',
)

# MIGRATIONS CONFIGURATION
# ------------------------------------------------------------------------------
MIGRATION_MODULES = {
    'sites': 'osmaxx.contrib.sites.migrations',
    'auth': 'osmaxx.contrib.auth.migrations',
    'stored_messages': 'osmaxx.third_party_apps.stored_messages.migrations',
}

# DEBUG
# ------------------------------------------------------------------------------
# See: https://docs.djangoproject.com/en/dev/ref/settings/#debug
DEBUG = env.bool("DJANGO_DEBUG", False)

# FIXTURE CONFIGURATION
# ------------------------------------------------------------------------------
# See: https://docs.djangoproject.com/en/dev/ref/settings/#std:setting-FIXTURE_DIRS
FIXTURE_DIRS = [
    str(APPS_DIR('fixtures')),
]

# EMAIL CONFIGURATION
# ------------------------------------------------------------------------------
EMAIL_BACKEND = env.str('DJANGO_EMAIL_BACKEND', default='django.core.mail.backends.smtp.EmailBackend')
EMAIL_HOST = env.str('DJANGO_EMAIL_HOST', default='localhost')
EMAIL_HOST_PASSWORD = env.str('DJANGO_EMAIL_HOST_PASSWORD', default='')
EMAIL_HOST_USER = env.str('DJANGO_EMAIL_HOST_USER', default='')
EMAIL_PORT = env.int('DJANGO_EMAIL_PORT', default=25)
EMAIL_SUBJECT_PREFIX = env.str('DJANGO_EMAIL_SUBJECT_PREFIX', default='[OSMaxx] ')
EMAIL_USE_TLS = env.bool('DJANGO_EMAIL_USE_TLS', default=False)
EMAIL_USE_SSL = env.bool('DJANGO_EMAIL_USE_SSL', default=False)
EMAIL_TIMEOUT = env.int('DJANGO_EMAIL_TIMEOUT', default=None)
EMAIL_SSL_CERTFILE = env.bool('DJANGO_EMAIL_SSL_CERTFILET', default=None)
EMAIL_SSL_KEYFILE = env.bool('DJANGO_EMAIL_SSL_KEYFILE', default=None)
DEFAULT_FROM_EMAIL = env.str('DJANGO_DEFAULT_FROM_EMAIL', default='webmaster@localhost')
SERVER_EMAIL = env.str('DJANGO_SERVER_EMAIL', default='root@localhost')

EMAIL_FILE_PATH = env.str('DJANGO_EMAIL_FILE_PATH', default=None)
# allow default setting (unset) if the variable isn't set in the environment
if not EMAIL_FILE_PATH:
    del EMAIL_FILE_PATH

# MANAGER CONFIGURATION
# ------------------------------------------------------------------------------
# See: https://docs.djangoproject.com/en/dev/ref/settings/#admins
ADMINS = ()

# See: https://docs.djangoproject.com/en/dev/ref/settings/#managers
MANAGERS = ADMINS

# DATABASE CONFIGURATION
# ------------------------------------------------------------------------------
# See: https://docs.djangoproject.com/en/dev/ref/settings/#databases
DATABASES = {
    # Raises ImproperlyConfigured exception if DATABASE_URL not in os.environ
    'default': env.db("DJANGO_DATABASE_URL", default="postgis://localhost/osmaxx"),
}
DATABASES['default']['ATOMIC_REQUESTS'] = True

# GENERAL CONFIGURATION
# ------------------------------------------------------------------------------
# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# In a Windows environment this must be set to your system time zone.
TIME_ZONE = 'Europe/Zurich'

# See: https://docs.djangoproject.com/en/dev/ref/settings/#language-code
LANGUAGE_CODE = 'en-us'

# See: https://docs.djangoproject.com/en/dev/ref/settings/#site-id
SITE_ID = 1

# See: https://docs.djangoproject.com/en/dev/ref/settings/#use-i18n
USE_I18N = True

# See: https://docs.djangoproject.com/en/dev/ref/settings/#use-l10n
USE_L10N = True

# See: https://docs.djangoproject.com/en/dev/ref/settings/#use-tz
USE_TZ = True

# TEMPLATE CONFIGURATION
# ------------------------------------------------------------------------------
# See: https://docs.djangoproject.com/en/1.8/ref/templates/upgrading/#the-templates-settings

_html_template_engine = {
    'BACKEND': 'django.template.backends.django.DjangoTemplates',
    'DIRS': [
        str(APPS_DIR.path('templates')),
    ],
    'OPTIONS': {
        'context_processors': [
            'django.contrib.auth.context_processors.auth',
            'django.template.context_processors.debug',
            'django.template.context_processors.i18n',
            'django.template.context_processors.media',
            'django.template.context_processors.static',
            'django.template.context_processors.tz',
            'django.contrib.messages.context_processors.messages',
            'social_django.context_processors.backends',
            'social_django.context_processors.login_redirect',
            'django.template.context_processors.request',
            'osmaxx.excerptexport.context_processors.message_adapter_context_processor'
        ],
        'loaders': [
            'django.template.loaders.filesystem.Loader',
            'django.template.loaders.app_directories.Loader',
        ]
    },
}
_plaintext_template_engine = deepcopy(_html_template_engine)
_plaintext_template_engine['NAME'] = 'plaintext'
_plaintext_template_engine['OPTIONS']['autoescape'] = False

TEMPLATES = [
    _html_template_engine,
    _plaintext_template_engine,
]


# STATIC FILE CONFIGURATION
# ------------------------------------------------------------------------------
# See: https://docs.djangoproject.com/en/dev/ref/settings/#static-root
STATIC_ROOT = env.str('DJANGO_STATIC_ROOT', default=str(ROOT_DIR('..', 'static')))

# See: https://docs.djangoproject.com/en/dev/ref/settings/#static-url
STATIC_URL = '/static/'

# See: https://docs.djangoproject.com/en/dev/ref/contrib/staticfiles/#std:setting-STATICFILES_DIRS
STATICFILES_DIRS = (
    # str(APPS_DIR('static')),
)

# See: https://docs.djangoproject.com/en/dev/ref/contrib/staticfiles/#staticfiles-finders
STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
)


# MEDIA CONFIGURATION
# ------------------------------------------------------------------------------
# See: https://docs.djangoproject.com/en/dev/ref/settings/#media-root

# data & media

MEDIA_ROOT = env.str('DJANGO_MEDIA_ROOT', default=str(ROOT_DIR('..', 'media')))

# See: https://docs.djangoproject.com/en/dev/ref/settings/#media-url
MEDIA_URL = '/media/'

# URL Configuration
# ------------------------------------------------------------------------------
ROOT_URLCONF = 'web_frontend.config.urls'

# See: https://docs.djangoproject.com/en/dev/ref/settings/#wsgi-application
WSGI_APPLICATION = 'web_frontend.config.wsgi.application'

AUTHENTICATION_BACKENDS = (
    'social_core.backends.open_id.OpenIdAuth',
    'social_core.backends.openstreetmap.OpenStreetMapOAuth',
    'django.contrib.auth.backends.ModelBackend',
)

SOCIAL_AUTH_OPENSTREETMAP_KEY = env.str('SOCIAL_AUTH_OPENSTREETMAP_KEY', '')
SOCIAL_AUTH_OPENSTREETMAP_SECRET = env.str('SOCIAL_AUTH_OPENSTREETMAP_SECRET', '')

SOCIAL_AUTH_PIPELINE = (
    # Get the information we can about the user and return it in a simple
    # format to create the user instance later. On some cases the details are
    # already part of the auth response from the provider, but sometimes this
    # could hit a provider API.
    'social_core.pipeline.social_auth.social_details',

    # Get the social uid from whichever service we're authing thru. The uid is
    # the unique identifier of the given user in the provider.
    'social_core.pipeline.social_auth.social_uid',

    # Verifies that the current auth process is valid within the current
    # project, this is were emails and domains whitelists are applied (if
    # defined).
    'social_core.pipeline.social_auth.auth_allowed',

    # Checks if the current social-account is already associated in the site.
    'social_core.pipeline.social_auth.social_user',

    # Make up a username for this person, appends a random string at the end if
    # there's any collision.
    'social_core.pipeline.user.get_username',

    # Send a validation email to the user to verify its email address.
    # Disabled by default.
    'social_core.pipeline.mail.mail_validation',

    # Associates the current social details with another user account with
    # a similar email address. Disabled by default.
    'social_core.pipeline.social_auth.associate_by_email',

    # Create a user account if we haven't found one yet.
    'social_core.pipeline.user.create_user',

    # Create the record that associated the social account with this user.
    'social_core.pipeline.social_auth.associate_user',

    # Populate the extra_data field in the social record with the values
    # specified by settings (and the default ones like access_token, etc).
    'social_core.pipeline.social_auth.load_extra_data',

    # Update the user record with any changed info from the auth service.
    'social_core.pipeline.user.user_details'
)


CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': '',
    }
}

# LOGGING CONFIGURATION
# ------------------------------------------------------------------------------
# See: https://docs.djangoproject.com/en/dev/ref/settings/#logging
# A sample logging configuration. The only tangible logging
# performed by this configuration is to send an email to
# the site admins on every HTTP 500 error when DEBUG=False.
# See http://docs.djangoproject.com/en/dev/topics/logging for
# more details on how to customize your logging configuration.
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': env.str('DJANGO_LOG_LEVEL', default='INFO'),
        },
        'osmaxx': {
            'handlers': ['console'],
            'level': env.str('DJANGO_LOG_LEVEL', default='INFO'),
        },
    },
}

# login url if param 'next' is not set
LOGIN_REDIRECT_URL = '/profile/edit/'
LOGIN_URL = '/login/'
LOGOUT_URL = '/logout/'
# TODO: show nice user error page
SOCIAL_AUTH_LOGIN_ERROR_URL = '/'
# Used to redirect the user once the auth process ended successfully.
# The value of ?next=/foo is used if it was present.
SOCIAL_AUTH_LOGIN_REDIRECT_URL = '/profile/edit/'
# Is used as a fallback for LOGIN_ERROR_URL
SOCIAL_AUTH_LOGIN_URL = '/'
# Used to redirect new registered users, will be used in place of SOCIAL_AUTH_LOGIN_REDIRECT_URL if defined.
SOCIAL_AUTH_NEW_USER_REDIRECT_URL = '/profile/edit/'
# Like SOCIAL_AUTH_NEW_USER_REDIRECT_URL but for new associated accounts (user is already logged in).
# Used in place of SOCIAL_AUTH_LOGIN_REDIRECT_URL
SOCIAL_AUTH_NEW_ASSOCIATION_REDIRECT_URL = '/profile/edit/'
# The user will be redirected to this URL when a social account is disconnected.
SOCIAL_AUTH_DISCONNECT_REDIRECT_URL = '/'
# Inactive users can be redirected to this URL when trying to authenticate.
# Successful URLs will default to SOCIAL_AUTH_LOGIN_URL while error URLs will fallback to SOCIAL_AUTH_LOGIN_ERROR_URL.
SOCIAL_AUTH_INACTIVE_USER_URL = '/'
SOCIAL_AUTH_LOGIN_SUCCESS_URL = '/profile/edit/'

SOCIAL_AUTH_ADMIN_USER_SEARCH_FIELDS = ['username', 'email']

POSTGIS_VERSION = (2, 1)

REST_FRAMEWORK = {
    # Use Django's standard `django.contrib.auth` permissions,
    # or allow read-only access for unauthenticated users.
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.DjangoModelPermissionsOrAnonReadOnly'
    ],
    'DEFAULT_RENDERER_CLASSES': (
        'rest_framework.renderers.JSONRenderer',
    ),
    'DEFAULT_PARSER_CLASSES': (
        'rest_framework.parsers.JSONParser',
    )
}


# Message-Storage Settings
MESSAGE_STORAGE = 'stored_messages.storage.PersistentStorage'

# Do not alter this once migrations have been run, since these values are stored in the database.
OSMAXX_FRONTEND_USER_GROUP = 'osmaxx_frontend_users'
REGISTRATION_OPEN = True  # If True, verified users are automatically being added to OSMAXX_FRONTEND_USER_GROUP

# message type mapping
MESSAGE_TAGS = {
    message_constants.DEBUG: 'debug',
    message_constants.INFO: 'info',
    message_constants.SUCCESS: 'success',
    message_constants.WARNING: 'warning',
    message_constants.ERROR: 'error',
    10: 'debug',
    20: 'info',
    25: 'success',
    30: 'warning',
    40: 'error'
}

OSMAXX = {
    'EXTRACTION_PROCESSING_TIMEOUT_TIMEDELTA': timezone.timedelta(
        hours=env.int('DJANGO_OSMAXX_EXTRACTION_PROCESSING_TIMEOUT_HOURS', default=48)
    ),
    'RESULT_FILE_AVAILABILITY_DURATION': timezone.timedelta(
        days=env.int('DJANGO_OSMAXX_RESULT_FILE_AVAILABILITY_DURATION_DAYS', default=14)
    ),
    'OLD_RESULT_FILES_REMOVAL_CHECK_INTERVAL': timezone.timedelta(
        hours=env.int('DJANGO_OSMAXX_OLD_RESULT_FILES_REMOVAL_CHECK_INTERVAL_HOURS', default=1)
    ),
    # The email adress of this user will be used to generate the mailto link for users
    # to request access to osmaxx (access_denied page)
    'ACCOUNT_MANAGER_EMAIL': env.str('OSMAXX_ACCOUNT_MANAGER_EMAIL', default=DEFAULT_FROM_EMAIL),
    'CONVERSION_SERVICE_URL': env.str('DJANGO_OSMAXX_CONVERSION_SERVICE_URL', default='http://localhost:8901/api/'),
    'CONVERSION_SERVICE_USERNAME': env.str('DJANGO_OSMAXX_CONVERSION_SERVICE_USERNAME', default='default_user'),
    'CONVERSION_SERVICE_PASSWORD': env.str('DJANGO_OSMAXX_CONVERSION_SERVICE_PASSWORD', default='default_password'),
    'EXCLUSIVE_USER_GROUP': 'osmaxx_high_priority',  # high priority people
    'SECURED_PROXY': env.bool('DJANGO_OSMAXX_SECURED_PROXY', False),
}

CRISPY_TEMPLATE_PACK = 'bootstrap3'

# Security - defaults taken from Django 1.8 (not secure enough for production)
SECRET_KEY = env.str("DJANGO_SECRET_KEY", default=None)
ALLOWED_HOSTS = env.list('DJANGO_ALLOWED_HOSTS', default=[])
X_FRAME_OPTIONS = env.str('DJANGO_X_FRAME_OPTIONS', default='SAMEORIGIN')

## General SECURE Settings
SECURE_BROWSER_XSS_FILTER = env.bool('DJANGO_SECURE_BROWSER_XSS_FILTER', default=False)
SECURE_CONTENT_TYPE_NOSNIFF = env.bool('DJANGO_SECURE_CONTENT_TYPE_NOSNIFF', default=False)
SECURE_HSTS_INCLUDE_SUBDOMAINS = env.bool('DJANGO_SECURE_HSTS_INCLUDE_SUBDOMAINS', default=False)
SECURE_HSTS_SECONDS = env.int('DJANGO_SECURE_HSTS_SECONDS', default=0)
SECURE_PROXY_SSL_HEADER = env.tuple('DJANGO_SECURE_PROXY_SSL_HEADER', default=None)
SECURE_REDIRECT_EXEMPT = env.list('DJANGO_SECURE_REDIRECT_EXEMPT', default=[])
SECURE_SSL_HOST = env.str('DJANGO_SECURE_SSL_HOST', default=None)
SECURE_SSL_REDIRECT = env.bool('DJANGO_SECURE_SSL_REDIRECT', default=False)

## CSRF
CSRF_COOKIE_SECURE = env.bool('DJANGO_CSRF_COOKIE_SECURE', default=False)
CSRF_COOKIE_HTTPONLY = env.bool('DJANGO_CSRF_COOKIE_HTTPONLY', default=False)
CSRF_COOKIE_DOMAIN = env.str('DJANGO_CSRF_COOKIE_DOMAIN', default=None)
CSRF_COOKIE_NAME = env.str('DJANGO_CSRF_COOKIE_NAME', default='csrftoken')
CSRF_COOKIE_PATH = env.str('DJANGO_CSRF_COOKIE_PATH', default='/')
CSRF_FAILURE_VIEW = env.str('DJANGO_CSRF_FAILURE_VIEW', default='django.views.csrf.csrf_failure')

## Sessions
SESSION_CACHE_ALIAS = env.str('DJANGO_SESSION_CACHE_ALIAS', default='default')
SESSION_COOKIE_AGE = env.int('DJANGO_SESSION_COOKIE_AGE', default=timedelta(weeks=2).total_seconds())
SESSION_COOKIE_DOMAIN = env.str('DJANGO_SESSION_COOKIE_DOMAIN', default=None)
SESSION_COOKIE_HTTPONLY = env.bool('DJANGO_SESSION_COOKIE_HTTPONLY', default=True)
SESSION_COOKIE_NAME = env.str('DJANGO_SESSION_COOKIE_NAME', default='sessionid')
SESSION_COOKIE_PATH = env.str('DJANGO_SESSION_COOKIE_PATH', default='/')
SESSION_COOKIE_SECURE = env.bool('DJANGO_SESSION_COOKIE_SECURE', default=False)
SESSION_ENGINE = env.str('DJANGO_SESSION_ENGINE', default='django.contrib.sessions.backends.db')
SESSION_EXPIRE_AT_BROWSER_CLOSE = env.bool('DJANGO_SESSION_EXPIRE_AT_BROWSER_CLOSE', default=False)
SESSION_FILE_PATH = env.str('DJANGO_SESSION_FILE_PATH', default=None)
SESSION_SAVE_EVERY_REQUEST = env.bool('DJANGO_SESSION_SAVE_EVERY_REQUEST', default=False)
SESSION_SERIALIZER = env.str('DJANGO_SESSION_SERIALIZER', default='django.contrib.sessions.serializers.JSONSerializer')

# RQ settings
REDIS_CONNECTION = dict(
    HOST=env.str('REDIS_HOST', default='localhost'),
    PORT=env.str('REDIS_PORT', default=6379),
    DB=0,
    PASSWORD='',
    DEFAULT_TIMEOUT=int(timedelta(days=2).total_seconds())
)
RQ_QUEUE_NAMES = ['default', 'high']
RQ_QUEUES = {name: REDIS_CONNECTION for name in RQ_QUEUE_NAMES}
