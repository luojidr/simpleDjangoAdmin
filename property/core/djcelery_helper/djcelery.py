from __future__ import absolute_import

import os
import logging
from collections import OrderedDict

from celery import Celery
from celery import platforms
from celery.signals import celeryd_init, celeryd_after_setup, beat_init, task_internal_error
from django.conf import settings, ENVIRONMENT_VARIABLE

from .conf import CeleryConfig
from .hooks.context import ContextTask
from .utils.webapp import run_with_thread


__all__ = ["app"]

worker_logger = logging.getLogger("celery.worker")
beat_cls = "%s.hooks.beat:Beat" % __name__.rsplit(".", 1)[0]

# Specifying the settings here means the celery command line program will know where your Django project is.
# This statement must always appear before the app instance is created, which is what we do next:
django_settings_module = os.getenv(ENVIRONMENT_VARIABLE)
logging.warning("Celery use `DJANGO_SETTINGS_MODULE`: %s", django_settings_module)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', django_settings_module)

main = settings.__dict__.get('APP_NAME', __name__)
app = Celery(main=main + '_celery', task_cls=ContextTask)
# app.set_current()
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
# app.autodiscover_tasks()

# 设置 BROKER_URL 后, 启动 worker 后可以探测所有任务,未启动无法探测
# i = app.control.inspect()  # 探测所有 worker
# print(i.registered_tasks())

# Pprint config
tips_kwargs = OrderedDict(
    broker_url=app.conf.broker_url,
    beat_scheduler=app.conf.beat_scheduler,
    beat_cls=beat_cls,
    amqp_cls=CeleryConfig.CELERY_NATIVE_AMQP
)
tips_msg = "\n\t".join(["%s: {%s}" % (k, k) for k in tips_kwargs])
logging.warning(('===>>> Celery Important Config:\n\t' + tips_msg).format(**tips_kwargs))


@app.task(bind=True)
def debug_task(self):
    print('Request: {0!r}'.format(self.request))  # dumps its own request information


@beat_init.connect
def unregister_when_beat_init(sender, **kwargs):
    unregister_useless_tasks()

    if getattr(settings, 'CELERY_WEBAPP', False):
        run_with_thread(signal=kwargs.get('signal'))


@celeryd_after_setup.connect
def unregister_after_worker_setup(sender, instance, **kwargs):
    unregister_useless_tasks()

    if getattr(settings, 'CELERY_WEBAPP', False):
        run_with_thread(signal=kwargs.get('signal'))


@task_internal_error.connect
def handle_task_internal_error(sender, task_id, args, kwargs, request, einfo, **kw):
    """ Handle errors in tasks by signal, that is not internal logic error in task func code.
        Because the result of a failed task execution is stored in result_backend
    """
    worker_logger.info("Sender<%s> was error: %s at task<%s>", sender, einfo, task_id)
    worker_logger.error("TaskId: %s, args: %s, kwargs: %s, request: %s", task_id, args, kwargs, request)


@celeryd_init.connect
def bind_do_watch_task(sender, instance, conf, options, **kwargs):
    from .utils.watcher import TaskWatcher
    TaskWatcher()  # Auto to register task, then connect to consumer MQ message


def unregister_useless_tasks():
    """ Eliminate task of useless or not expected """
    from celery import current_app

    celery_tasks = current_app.tasks
    tasks = {task_name: task for task_name, task in celery_tasks.items()}

    for fun_name in CeleryConfig.CELERY_NOT_IMPORTS_TASKS:
        for complete_task_name, task in tasks.items():
            if fun_name == task.__name__:
                celery_tasks.unregister(complete_task_name)
