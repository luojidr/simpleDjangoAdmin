from __future__ import absolute_import

import os
import logging

from celery import Celery
from celery import platforms
from django.conf import settings

from config.settings import Config
from config.conf.celery import CeleryConfig
from property.core.mq.context import ContextTask

__all__ = ["app"]

# Specifying the settings here means the celery command line program will know where your Django project is.
# This statement must always appear before the app instance is created, which is what we do next:
logging.warning("Celery use `DJANGO_SETTINGS_MODULE` config: %s" % Config.DJANGO_SETTINGS_MODULE)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', Config.DJANGO_SETTINGS_MODULE)

app = Celery(settings.APP_NAME + '_celery', task_cls=ContextTask)
platforms.C_FORCE_ROOT = True       # celery不能用root用户启动问题

# This means that you don't have to use multiple configuration files, and instead configure Celery directly from the
# Django settings. You can pass the object directly here, but using a string is better since then the worker doesn't
# have to serialize the object.
# Not use `namespace` param, because of effect celery standard configuration
# https://docs.celeryproject.org/en/v4.4.7/userguide/configuration.html
app.config_from_object(obj=CeleryConfig)

# With the line above Celery will automatically discover tasks in reusable apps if you define all tasks in a separate
# tasks.py module. The tasks.py should be in dir which is added to INSTALLED_APP in settings.py. So you do not have
# to manually add the individual modules to the CELERY_IMPORTS in settings.py.
# app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)
# app.autodiscover_tasks()      # 有 CELERY_IMPORTS 配置，可以不需要 autodiscover_tasks()


@app.task(bind=True)
def debug_task(self):
    print('Request: {0!r}'.format(self.request))  # dumps its own request information
