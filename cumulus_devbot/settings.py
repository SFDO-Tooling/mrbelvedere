# Django settings for cumulus_devbot project.
import os

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))

DEBUG = os.environ.get('DEBUG', True)
if DEBUG in ('false','False'):
    DEBUG = False

#SECURE_SSL_REDIRECT = os.environ.get('SECURE_SSL_REDIRECT') == 'True'
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# Get admins from env variable in format jdoe@mailinator.com,John Doe
admins = os.environ.get('ADMINS', None)
if admins:
    try:
        admin_email, admin_name = admins.split(',')
        ADMINS = ((admin_name, admin_email),)
    except:
        ADMINS = ()
        
else:
    ADMINS = ()

MANAGERS = ADMINS

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3', # Add 'postgresql_psycopg2', 'mysql', 'sqlite3' or 'oracle'.
        'NAME': 'devbot.db',                      # Or path to database file if using sqlite3.
        # The following settings are not used with sqlite3:
        'USER': '',
        'PASSWORD': '',
        'HOST': '',                      # Empty for localhost through domain sockets or '127.0.0.1' for localhost through TCP.
        'PORT': '',                      # Set to empty string for default.
    }
}

# Parse database configuration from $DATABASE_URL
import dj_database_url
DATABASES['default'] =  dj_database_url.config(default='sqlite:///devbot.db')

# Hosts/domain names that are valid for this site; required if DEBUG is False
# See https://docs.djangoproject.com/en/1.5/ref/settings/#allowed-hosts
ALLOWED_HOSTS = []

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# In a Windows environment this must be set to your system time zone.
TIME_ZONE = 'America/Los_Angeles'

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'en-us'

SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# If you set this to False, Django will not format dates, numbers and
# calendars according to the current locale.
USE_L10N = True

# If you set this to False, Django will not use timezone-aware datetimes.
USE_TZ = True

# Absolute filesystem path to the directory that will hold user-uploaded files.
# Example: "/var/www/example.com/media/"
MEDIA_ROOT = ''

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash.
# Examples: "http://example.com/media/", "http://media.example.com/"
MEDIA_URL = ''

# Absolute path to the directory static files should be collected to.
# Don't put anything in this directory yourself; store your static files
# in apps' "static/" subdirectories and in STATICFILES_DIRS.
# Example: "/var/www/example.com/static/"
STATIC_ROOT = ''

# URL prefix for static files.
# Example: "http://example.com/static/", "http://static.example.com/"
STATIC_URL = '/static/'

# Additional locations of static files
STATICFILES_DIRS = (
    # Put strings here, like "/home/html/static" or "C:/www/django/static".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
)

# List of finder classes that know how to find static files in
# various locations.
STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
#    'django.contrib.staticfiles.finders.DefaultStorageFinder',
)

# Make this unique, and don't share it with anybody.
SECRET_KEY = '-)3=k_d8821*k+v0cm&unyc429hm&tfs%#6y(ndk*%+l4a+7+('

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.contrib.auth.context_processors.auth',
                'django.template.context_processors.debug',
                'django.template.context_processors.i18n',
                'django.template.context_processors.media',
                'django.template.context_processors.static',
                'django.template.context_processors.tz',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'social.apps.django_app.context_processors.backends',
                'social.apps.django_app.context_processors.login_redirect',
            ],
            'debug': DEBUG,
        },
    },
]

MIDDLEWARE_CLASSES = (
    'hirefire.contrib.django.middleware.HireFireMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    #'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    # Uncomment the next line for simple clickjacking protection:
    # 'django.middleware.clickjacking.XFrameOptionsMiddleware',
)

ROOT_URLCONF = 'cumulus_devbot.urls'

# Python dotted path to the WSGI application used by Django's runserver.
WSGI_APPLICATION = 'cumulus_devbot.wsgi.application'

PROJECT_DIR = os.path.dirname(__file__) # this is not Django setting.

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.admin',
    'django.contrib.admindocs',
    'django_rq',
    'bootstrap3',
    'mpinstaller',
    'contributor',
    'djng',
    'cumulus_devbot',
    'tinymce',
    'rest_framework',
    'api',
    'social.apps.django_app.default',
    'crispy_forms',
    'django_slds',
    'django_slds_crispyforms',
)

AUTHENTICATION_BACKENDS = [
    'social.backends.github.GithubOAuth2',
    'django.contrib.auth.backends.ModelBackend',
]

# GitHub OAuth config
SOCIAL_AUTH_GITHUB_KEY = os.environ.get('SOCIAL_AUTH_GITHUB_KEY')
SOCIAL_AUTH_GITHUB_SECRET = os.environ.get('SOCIAL_AUTH_GITHUB_SECRET')
SOCIAL_AUTH_GITHUB_SCOPE = os.environ.get('SOCIAL_AUTH_GITHUB_SCOPE')
if SOCIAL_AUTH_GITHUB_SCOPE:
    SOCIAL_AUTH_GITHUB_SCOPE = SOCIAL_AUTH_GITHUB_SCOPE.split(',')
else:
    SOCIAL_AUTH_GITHUB_SCOPE = ['public_repo', ]
LOGIN_URL = '/login/github/'
LOGIN_REDIRECT_URL = '/contributor'

#LOGIN_ERROR_URL = '/login-error/'

SESSION_SERIALIZER = 'django.contrib.sessions.serializers.JSONSerializer'

# A sample logging configuration. The only tangible logging
# performed by this configuration is to send an email to
# the site admins on every HTTP 500 error when DEBUG=False.
# See http://docs.djangoproject.com/en/dev/topics/logging for
# more details on how to customize your logging configuration.
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse'
        },
    },
    "formatters": {
        "rq_console": {
            "format": "%(asctime)s %(message)s",
            "datefmt": "%H:%M:%S",
        },
    },
    'handlers': {
        'mail_admins': {
            'level': 'ERROR',
            'filters': ['require_debug_false'],
            'class': 'django.utils.log.AdminEmailHandler'
        },
        "rq_console": {
            "level": "DEBUG",
            "class": "rq.utils.ColorizingStreamHandler",
            "formatter": "rq_console",
            "exclude": ["%(asctime)s"],
        },
    },
    'loggers': {
        'django.request': {
            'handlers': ['mail_admins'],
            'level': 'ERROR',
            'propagate': True,
        },
        "rq.worker": {
            "handlers": ["rq_console",],
            "level": "DEBUG",
        },
    }
}

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.db.DatabaseCache',
        'LOCATION': 'cache',
    }
}

# Honor the 'X-Forwarded-Proto' header for request.is_secure()
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# Allow all host headers
ALLOWED_HOSTS = ['*']

# Static asset configuration
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_ROOT = 'staticfiles'
STATIC_URL = '/static/'

STATICFILES_DIRS = (
    os.path.join(BASE_DIR, 'static'),
)

EMAIL_HOST_USER = os.environ.get('SENDGRID_USERNAME', None)
EMAIL_HOST= 'smtp.sendgrid.net'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_PASSWORD = os.environ.get('SENDGRID_PASSWORD', None)

# Heroku doesn't pass remote ip in REMOTE_ADDR, you have to parse
# the first ip from HTTP_X_FORWARDED_FOR to get the remote ip
USE_X_FORWARDED_HOST = True

RQ_QUEUES = {
    'default': {
        'URL': os.getenv('REDISTOGO_URL', 'redis://localhost:6379'), # If you're on Heroku
        'DB': 0,
        'timeout': 1800,
    },
    'high': {
        'URL': os.getenv('REDISTOGO_URL', 'redis://localhost:6379'), # If you're on Heroku
        'DB': 0,
        'timeout': 1800,
    },
    'low': {
        'URL': os.getenv('REDISTOGO_URL', 'redis://localhost:6379'), # If you're on Heroku
        'DB': 0,
        'timeout': 1800,
    },
}

MPINSTALLER_CLIENT_ID = os.environ.get('MPINSTALLER_CLIENT_ID')
MPINSTALLER_CLIENT_SECRET = os.environ.get('MPINSTALLER_CLIENT_SECRET')
MPINSTALLER_CALLBACK_URL = os.environ.get('MPINSTALLER_CALLBACK_URL')

SAUCELABS_USER = os.environ.get('SAUCELABS_USER')
SAUCELABS_KEY = os.environ.get('SAUCELABS_KEY')

HIREFIRE_PROCS = ['cumulus_devbot.procs.WorkerProc',]

TINYMCE_DEFAULT_CONFIG = {
    'plugins': "table,paste,searchreplace",
    'theme': "advanced",
    'custom_undo_redo_levels': 10,
}

REST_FRAMEWORK = {
    # Use hyperlinked styles by default.
    # Only used if the `serializer_class` attribute is not set on a view.
    'DEFAULT_MODEL_SERIALIZER_CLASS':
        'rest_framework.serializers.HyperlinkedModelSerializer',

    # Use Django's standard `django.contrib.auth` permissions,
    # or allow read-only access for unauthenticated users.
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.DjangoModelPermissionsOrAnonReadOnly'
    ]
}

GOOGLE_ANALYTICS_CODE = os.environ.get('GOOGLE_ANALYTICS_CODE', None)
GOOGLE_ANALYTICS_ORG = os.environ.get('GOOGLE_ANALYTICS_ORG', None)

# django-cripsy-forms config
CRISPY_TEMPLATE_PACK='bootstrap3'

# Support svg maps
import mimetypes

mimetypes.add_type("image/svg+xml", ".svg", True)
mimetypes.add_type("image/svg+xml", ".svgz", True)

CRISPY_TEMPLATE_PACK = 'crispy_slds'
CRISPY_ALLOWED_TEMPLATE_PACKS = ('bootstrap', 'crispy_slds')

RQ_SYNC = os.environ.get('RQ_SYNC')
if RQ_SYNC:
    for queueConfig in RQ_QUEUES.itervalues():
        queueConfig['ASYNC'] = False

# Configurable site logo
SITE_LOGO_IMAGE_URL=os.environ.get('SITE_LOGO_IMAGE_URL')
SITE_LOGO_LINK_URL=os.environ.get('SITE_LOGO_LINK_URL')
SITE_LOGO_ALT_TEXT=os.environ.get('SITE_LOGO_ALT_TEXT')
