from .base import *  # noqa
from .base import env

# Database
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/3.0/ref/settings/#databases
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'property_dev',
        'HOST': '127.0.0.1',      # 192.168.190.128 | Root!1234
        'PORT': 3306,
        'USER': 'root',
        'PASSWORD': 'root',
        # 'PASSWORD': 'Root!1234',
    },

    'default_slave': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'property_dev_slave',
        'HOST': '127.0.0.1',
        'PORT': 3306,
        'USER': 'root',
        'PASSWORD': 'root',
        # 'PASSWORD': 'Root!1234',
    },
}


# APPS
# ------------------------------------------------------------------------------
# Application definition
INSTALLED_APPS += [
    # "debug_toolbar",
    # "rest_framework_swagger",
]


# GENERAL
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#debug
DEBUG = True
# https://docs.djangoproject.com/en/dev/ref/settings/#secret-key
SECRET_KEY = env(
    "DJANGO_SECRET_KEY",
    default="n20IAqHopdmar3ipc31YXe9fhoJ1NSM9N1PoEYZbAEuX8cZpGJxttaiJwm3jvcUZ",
)
# https://docs.djangoproject.com/en/dev/ref/settings/#allowed-hosts
ALLOWED_HOSTS = ["*", "0.0.0.0"]


# Djano-Debug-Toolbar
# ------------------------------------------------------------------------------
# https://django-debug-toolbar.readthedocs.io/en/latest/


# CACHES
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#caches

# CACHES = {
#     "default": {
#         "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
#         "LOCATION": "",
#     }
# }

CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": "redis://127.0.0.1:6379/0",
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
            "CONNECTION_POOL_KWARGS": {"max_connections": 100},
            "PASSWORD": "",
        }
    },

    "session": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": "redis://127.0.0.1:6379/1",
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
            "CONNECTION_POOL_KWARGS": {"max_connections": 100},
            "PASSWORD": "",
        }
    },
}

# Rest Framework Swagger
# ------------------------------------------------------------------------------
SWAGGER_SETTINGS = {
    "JSON_EDITOR": True,
}


# LOGGING
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#logging
LOGGING["loggers"].update({
    "django.db.backends": {
        "level": "DEBUG",
        "handlers": ["console"],
        # "handlers": ["sql_backend", "console"],
        "propagate": True,
    },
})


# EMAIL
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#email-backend
EMAIL_BACKEND = env(
    "DJANGO_EMAIL_BACKEND", default="django.core.mail.backends.smtp.EmailBackend"
)
EMAIL_HOST = "smtp.163.com"
EMAIL_HOST_USER = "xutaoding@163.com"
EMAIL_HOST_PASSWORD = "XKGDBTOTKUPSDEQQ"
EMAIL_USE_TLS = False
EMAIL_PORT = 25
EMAIL_FROM = "xutaoding@163.com"
DEFAULT_FROM_EMAIL = "xutaoding@163.com"

# WhiteNoise
# ------------------------------------------------------------------------------
# http://whitenoise.evans.io/en/latest/django.html#using-whitenoise-in-development
# WhiteNoise effect `django-debug-toolbar` static files
# INSTALLED_APPS = ["whitenoise.runserver_nostatic"] + INSTALLED_APPS  # noqa F405


# # django-debug-toolbar
# # ------------------------------------------------------------------------------
# # https://django-debug-toolbar.readthedocs.io/en/latest/installation.html#prerequisites
# # https://marcgibbons.com/django-rest-swagger/#installation
# INSTALLED_APPS += ["debug_toolbar", "rest_framework_swagger"]  # noqa F405
# # https://django-debug-toolbar.readthedocs.io/en/latest/installation.html#middleware
# MIDDLEWARE += ["debug_toolbar.middleware.DebugToolbarMiddleware"]  # noqa F405
# # https://django-debug-toolbar.readthedocs.io/en/latest/configuration.html#debug-toolbar-config
# DEBUG_TOOLBAR_CONFIG = {
#     "DISABLE_PANELS": ["debug_toolbar.panels.redirects.RedirectsPanel"],
#     "SHOW_TEMPLATE_CONTEXT": True,
#     'JQUERY_URL': r"http://code.jquery.com/jquery-2.1.1.min.js",
# }
# # https://django-debug-toolbar.readthedocs.io/en/latest/installation.html#internal-ips
# INTERNAL_IPS = ["127.0.0.1"]


# Django Rest Swagger
# ------------------------------------------------------------------------------
# https://django-rest-swagger.readthedocs.io/en/latest/#django-rest-swagger

REST_FRAMEWORK.update(
    {
        "DEFAULT_SCHEMA_CLASS": "rest_framework.schemas.coreapi.AutoSchema"
    }
)

# Celery
# ------------------------------------------------------------------------------
# http://docs.celeryproject.org/en/latest/userguide/configuration.html#task-always-eager
# CELERY_TASK_ALWAYS_EAGER = True
# http://docs.celeryproject.org/en/latest/userguide/configuration.html#task-eager-propagates
# CELERY_TASK_EAGER_PROPAGATES = True
# Your stuff...
# ------------------------------------------------------------------------------


