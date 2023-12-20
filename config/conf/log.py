import os.path

app_name = 'property'
LOG_DIR = "/data/logs/%s" % app_name
os.makedirs(LOG_DIR, exist_ok=True)

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,

    "formatters": {
        "verbose": {
            "format": "[%(asctime)s] [%(filename)s:%(lineno)d] [%(module)s:%(funcName)s] %(levelname)s %(message)s"
        }
    },

    "filters": {
        'require_debug_true': {
            '()': 'django.utils.log.RequireDebugTrue',
        },
    },

    "handlers": {
        "console": {
            "level": "DEBUG",
            "filters": ["require_debug_true"],
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },

        "django": {
            "level": 'INFO',
            "class": 'logging.handlers.RotatingFileHandler',
            "filename": os.path.join(LOG_DIR, "{0}.log".format(app_name)),
            "formatter": 'verbose',
            'maxBytes': 1024 * 1024 * 300,
            'backupCount': 10,
            'encoding': 'utf-8',
          },

        "sql_backend": {
            "level": 'INFO',
            "class": 'logging.handlers.RotatingFileHandler',
            "filename": os.path.join(LOG_DIR, "{0}_sql.log".format(app_name)),
            "formatter": 'verbose',
            'maxBytes': 1024 * 1024 * 300,
            'backupCount': 10,
            'encoding': 'utf-8',
          },

        "celery_task": {
            "level": 'INFO',
            "class": 'logging.handlers.RotatingFileHandler',
            "filename": os.path.join(LOG_DIR, "{0}_celery_task.log".format(app_name)),
            "formatter": 'verbose',
            'maxBytes': 1024 * 1024 * 300,
            'backupCount': 10,
            'encoding': 'utf-8',
          },

        "celery_worker": {
            "level": 'INFO',
            "class": 'logging.handlers.RotatingFileHandler',
            "filename": os.path.join(LOG_DIR, "{0}_celery_worker.log".format(app_name)),
            "formatter": 'verbose',
            'maxBytes': 1024 * 1024 * 300,
            'backupCount': 10,
            'encoding': 'utf-8',
          },
    },

    "root": {"level": "INFO", "handlers": ["console"]},

    "loggers": {
        "django": {
            "level": "INFO",
            "handlers": ["console", "django"],
            "propagate": True,
        },

        # Errors logged by the SDK itself
        "sentry_sdk": {
            "level": "INFO",
            "handlers": ["django"],
            "propagate": False
        },

        "celery.task": {
            "level": "INFO",
            "handlers": ["celery_task"],
            "propagate": False
        },

        "celery.worker": {
            "level": "INFO",
            "handlers": ["celery_worker"],
            "propagate": False
        },

        "django.security.DisallowedHost": {
            "level": "ERROR",
            "handlers": ["console"],
            "propagate": False,
        },
    },
}
