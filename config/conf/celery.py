import os.path
import importlib
import logging
import pathlib
import pkgutil

from django.conf import settings
from kombu import Exchange, Queue
from celery.schedules import crontab

from config.settings import Config

_app_env = settings.APP_ENV
logging.warning("CeleryConfig go into env[%s]", _app_env)

__all__ = ["CeleryConfig"]


def _autodiscover_dj_tasks():
    """ 自动发现 django app 任务, 兼容应用目录task, 规则如下:
    Rules:
        (1): 优先加载 tasks 目录
            tasks/
                task_aaa.py
                task_bbb.py
        (2): 应用目录 tasks.py 文件
    """
    TASKS = "tasks"
    all_task_list = []
    project_name = settings.APP_NAME

    if not os.getenv("DJANGO_SETTINGS_MODULE"):
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', Config.DJANGO_SETTINGS_MODULE)
        logging.warning("autodiscover_dj_tasks --->>> config: [%s]", Config.DJANGO_SETTINGS_MODULE)

    for app_name in settings.INSTALLED_APPS:
        package = importlib.import_module(app_name)
        file_path = os.path.dirname(os.path.abspath(package.__file__))
        package_name = package.__package__

        for module_info in pkgutil.iter_modules(package.__path__, package.__name__ + "."):
            mod_name = module_info.name

            if mod_name == package_name + "." + TASKS:
                path = pathlib.Path(file_path)
                parent_parts_list = path.parent.parts
                app_path_list = list(parent_parts_list[parent_parts_list.index(project_name) + 1:])

                if not module_info.ispkg:
                    app_task_path = ".".join(app_path_list + [mod_name])
                    all_task_list.append(app_task_path)

                    logging.warning("autodiscover_dj_tasks --->>> task path: %s", app_task_path)
                else:
                    task_path = path / TASKS
                    sub_mod_info_list = list(pkgutil.iter_modules([str(task_path)]))

                    for sub_mod_info in sub_mod_info_list:
                        app_task_path = ".".join(app_path_list + [mod_name, sub_mod_info.name])
                        all_task_list.append(app_task_path)

                        logging.warning("autodiscover_dj_tasks --->>> task path: %s", app_task_path)

    logging.warning("======>>>>> The discovery tasks are as below\n")
    return all_task_list


class BaseConfig(object):
    """ Celery基本配置
    令人奇怪的原因：大写的配置可能会造成配置无效，eg: CELERY_BEAT_SCHEDULE；
    建议使用小写，如果使用大写：一定要检查版本是否支持
    """

    CELERY_TIMEZONE = "Asia/Shanghai"
    CELERY_ENABLE_UTC = False

    # 任务发送完成是否需要确认，对性能会稍有影响
    CELERY_ACKS_LATE = True

    # # 非常重要,有些情况下可以防止死锁 (celery4.4.7可能没有这个配置)
    CELERYD_FORCE_EXECV = True

    # 并发worker数, 也是命令行-c指定的数目
    # CELERYD_CONCURRENCY = os.cpu_count() * 4

    # 每个worker执行了多少个任务就死掉
    CELERYD_MAX_TASKS_PER_CHILD = 1000

    # 表示每个 worker 预取多少个消息,默认每个启动的worker下有 cpu_count 个子 worker 进程
    # 所有 worker 预取消息数量: cpu_count * CELERYD_PREFETCH_MULTIPLIER
    CELERYD_PREFETCH_MULTIPLIER = 10

    # celery日志存储位置 (celery4.4.7可能没有这个配置)
    # CELERYD_LOG_FILE = "/data/logs/fosun_circle/circle_celery.log"

    CELERY_ACCEPT_CONTENT = ['json', ]      # 指定任务接收的内容序列化类型
    CELERY_SERIALIZER = "json"
    CELERY_TASK_SERIALIZER = 'json'         # 任务序列化方式
    CELERY_RESULT_SERIALIZER = "json"       # 任务结果序列化方式

    # CELERY_TASK_RESULT_EXPIRES = 12 * 30    # 任务超过时间
    # CELERY_MESSAGE_COMPRESSION = 'zlib'       # 是否压缩

    # django-celery-results
    # # -----------------------------------------------------------------------
    # https://docs.celeryproject.org/en/latest/django/first-steps-with-django.html
    CELERY_RESULT_BACKEND = 'django-db'   # Default
    CELERY_RESULT_BACKEND_REDIS = 'redis://:@127.0.0.1:6379/0'    # 自定义
    CELERY_RESULT_BACKEND_FILE = 'file:///data/fs_results'     # 自定义
    CELERY_TASK_TO_BACKEND = "task_to_backend"                    # 自定义-任务结果存储到不同介质
    CELERY_CACHE_BACKEND = 'django-cache'

    DJANGO_CELERY_BEAT_TZ_AWARE = False     # ???
    # 调度器
    CELERYBEAT_SCHEDULER = "django_celery_beat.schedulers:DatabaseScheduler"

    # 拦截根日志配置
    CELERYD_HIJACK_ROOT_LOGGER = False


class CeleryQueueRouteConfig(object):
    """ RabbitMq Queue """

    CELERY_IMPORTS = _autodiscover_dj_tasks()

    CELERY_QUEUES = (
        # 例子
        Queue(
            name="sync_users_q", exchange=Exchange("sync_users_exc"), routing_key="sync_users_rk",
            queue_arguments={"x-max-priority": 2},

            # 数字越大， 消费者优先级越高
            consumer_arguments={"x-priority": 9},
        ),

        Queue(
            name="test_concurrency_limit_q",
            exchange=Exchange("test_concurrency_limit_exc"),
            routing_key="test_concurrency_limit_rk",
        ),

        Queue(
            name="async_test_timeout_decorator_q",
            exchange=Exchange("async_test_timeout_decorator_exc"),
            routing_key="async_test_timeout_decorator_rk",
        ),

        Queue(
            name="test_retry_message_q",
            exchange=Exchange("test_retry_message_exc"),
            routing_key="test_retry_message_rk",
        ),


        Queue(
            name="async_send_raw_message_q",
            exchange=Exchange("async_send_raw_message_exc"),
            routing_key="async_send_raw_message_rk",
        ),
    )

    CELERY_ROUTES = {
        "property.apps.users.tasks.task_spider_users.sync_users_from_spider": {
            "queue": "sync_users_q", "routing_key": "sync_users_rk"
        },

        "property.apps.users.tasks.task_concurrency_limit.test_concurrency_limit": {
            "queue": "test_concurrency_limit_q", "routing_key": "test_concurrency_limit_rk"
        },

        "property.apps.users.tasks.task_timeout_decorator.async_test_timeout_decorator": {
            "queue": "async_test_timeout_decorator_q", "routing_key": "async_test_timeout_decorator_rk"
        },

        "property.apps.users.tasks.task_timeout_decorator.test_retry_message": {
            "queue": "test_retry_message_q", "routing_key": "test_retry_message_rk"
        },

        "property.apps.users.tasks.task_timeout_decorator.async_send_raw_message": {
            "queue": "async_send_raw_message_q", "routing_key": "async_send_raw_message_rk"
        },
    }


class CeleryConfig(BaseConfig, CeleryQueueRouteConfig):
    """ Celery 配置文件 """

    APP_ENV = _app_env

    if APP_ENV == "DEV":
        BROKER_URL = "amqp://admin:admin013431@127.0.0.1:5672/%2Fproperty"
    else:
        BROKER_URL = "amqp://admin:admin013431_Prd@127.0.0.1:5672/%2Fproperty"

    # ******************** 定时任务 ********************
    # CELERYBEAT_SCHEDULE = {
    #     'sync_users_from_spider': {
    #         'task': 'property.apps.users.tasks.task_timeout_decorator.async_send_raw_message',
    #         'schedule': crontab(hour=0, minute=10),
    #         'args': (),
    #     },

        # 'send_user_info': {
        #     'task': 'fosun_circle.apps.users.tasks.send_user_info',
        #     'schedule': crontab(hour=0, minute=10),
        #     'args': (),
        # },
    # }
    # ******************** 定时任务 ********************




