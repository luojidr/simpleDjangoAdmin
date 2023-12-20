from .base import *  # noqa
from .base import env

# GENERAL
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#secret-key
SECRET_KEY = env(
    "DJANGO_SECRET_KEY",
    default="wj*u^fjsr-x)nm^d&&f%^6x2*vt10ll$m515&zs@tt+8eb2syk"
)
# https://docs.djangoproject.com/en/dev/ref/settings/#allowed-hosts
ALLOWED_HOSTS = env.list("DJANGO_ALLOWED_HOSTS", default=["*"])


# DATABASES
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/3.0/ref/settings/#databases
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'property_prod',
        'HOST': '172.24.51.219',
        'PORT': 3306,
        'USER': 'dingxt',
        'PASSWORD': 'dingxt5869_Prod',
        "POOL_OPTIONS": {
            "POOL_SIZE": 20,
            "MAX_OVERFLOW": 20
        }
    },

    'default_slave': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'property_prod',
        'HOST': '172.24.51.219',
        'PORT': 3306,
        'USER': 'dingxt',
        'PASSWORD': 'dingxt5869_Prod',
        "POOL_OPTIONS": {
            "POOL_SIZE": 20,
            "MAX_OVERFLOW": 20
        }
    },
}


# CACHES
# ------------------------------------------------------------------------------

CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": "redis://127.0.0.1:6399/6",
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
            "CONNECTION_POOL_KWARGS": {"max_connections": 100},
            "PASSWORD": "redis_Prod",

            # # Mimicing memcache behavior.
            # # http://jazzband.github.io/django-redis/latest/#_memcached_exceptions_behavior
            # "IGNORE_EXCEPTIONS": True,
        }
    }
}


# STATIC
# ------------------------------------------------------------------------------
# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/3.0/howto/static-files/
