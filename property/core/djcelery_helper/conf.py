import os
import logging

import environ
from kombu import Exchange, Queue
from celery.schedules import crontab

from .utils.autodiscover import autodiscover_task_imports, autodiscover_task_list

env = environ.Env()
_APP_ENV = env.str("APP_ENV", "DEV")

logging.warning("CeleryConfig go into env[%s]", _APP_ENV)

__all__ = ["CeleryConfig"]


class BaseConfig(object):
    """ Celery basic configuration """
    # ################################# Celery Standard Configuration ################################
    CELERY_TIMEZONE = "Asia/Shanghai"
    CELERY_ENABLE_UTC = False

    # 任务发送完成是否需要确认，对性能会稍有影响
    CELERY_ACKS_LATE = True

    # 非常重要, 有些情况下可以防止死锁 (celery4.4.7可能没有这个配置)
    CELERYD_FORCE_EXECV = True

    # 并发worker数, 也是命令行 -c 指定的数目
    # CELERYD_CONCURRENCY = os.cpu_count()

    # 每个 worker 执行了多少个任务就死掉，建议数量大一些, 一定程度上可以解决内存泄漏的情况
    CELERYD_MAX_TASKS_PER_CHILD = 100

    # 表示每个 worker 预取多少个消息, 默认每个启动的 worker 下有 cpu_count 个子 worker 进程
    # 所有 worker 预取消息数量: cpu_count * CELERYD_PREFETCH_MULTIPLIER
    CELERYD_PREFETCH_MULTIPLIER = 5

    # celery日志存储位置 (celery4.4.7可能没有这个配置)
    # CELERYD_LOG_FILE = "/data/logs/myproject/circle_celery.log"

    CELERY_ACCEPT_CONTENT = ['json', ]      # 任务接受的序列化类型
    CELERY_SERIALIZER = "json"
    CELERY_TASK_SERIALIZER = 'json'         # 指定任务的序列化方式
    CELERY_RESULT_SERIALIZER = "json"       # 任务执行结果序列化方式

    # django-celery-results
    # ---------------------------------------------------------------------------
    # https://docs.celeryproject.org/en/latest/django/first-steps-with-django.html
    CELERY_RESULT_BACKEND = 'django-db'
    # CELERY_RESULT_BACKEND = 'redis://:123456@127.0.0.1:6399/0'

    # https://docs.celeryq.dev/en/latest/django/first-steps-with-django.html#django-celery-results
    #     CACHES = {
    #         "django-cache": {
    #             "BACKEND": "django_redis.cache.RedisCache",
    #             "LOCATION": "redis://127.0.0.1:6379/0",
    #             "KEY_PREFIX": "circle",
    #             "OPTIONS": {
    #                 "CLIENT_CLASS": "django_redis.client.DefaultClient",
    #                 "CONNECTION_POOL_KWARGS": {"max_connections": 100, "decode_responses": True},
    #                 "PASSWORD": None,
    #             }
    #         },
    #     }
    CELERY_CACHE_BACKEND = 'django-cache'  # settings.CACHES中必须有此项: django-cache

    # CELERY_RESULT_EXPIRES = 10 * 60  # 任务结果的过期时间，定期(periodic)任务好像会自动清理

    # `django-celery-beat` DatabaseScheduler
    # CELERYBEAT_SCHEDULER = "django_celery_beat.schedulers:DatabaseScheduler"
    CELERYBEAT_SCHEDULER = "%s.hooks.schedulers:DatabaseScheduler" % __name__.rsplit(".", 1)[0]

    # CELERY_TRACK_STARTED = True

    # 拦截根日志配置，默认true，先前所有的logger的配置都会失效，可以通过设置false禁用定制自己的日志处理程序
    CELERYD_HIJACK_ROOT_LOGGER = False
    CELERYD_LOG_COLOR = True  # 是否开启不同级别的颜色标记，默认开启

    # 设置celery全局的日志格式；默认格式："[%(asctime)s: %(levelname)s/%(processName)s] %(message)s"
    # CELERYD_LOG_FORMAT = ''
    # 设置任务日志格式，默认："[%(asctime)s: %(levelname)s/%(processName)s [%(task_name)s(%(task_id)s)] %(message)s"
    # CELERYD_TASK_LOG_FORMAT = ''

    # 去掉心跳机制
    BROKER_HEARTBEAT = 0

    # 限制任务的执行频率
    # CELERY_ANNOTATIONS = {'tasks.add': {'rate_limit': '10/s'}}  # 限制tasks模块下的add函数，每秒钟只能执行10次
    # CELERY_ANNOTATIONS = {'*': {'rate_limit': '10/s'}}  # 限制所有的任务的刷新频率

    # CELERY_TASK_RESULT_EXPIRES = 1200     # 任务过期时间, celery任务执行结果的超时时间
    # CELERYD_TASK_TIME_LIMIT = 60          # 单个任务的运行时间限制，否则执行该任务的worker将被杀死，任务移交给父进程
    # CELERY_DISABLE_RATE_LIMITS = True     # 关闭限速
    # CELERY_MESSAGE_COMPRESSION = 'zlib'           # 压缩方案选择，可以是zlib, bzip2，默认是发送没有压缩的数据

    # 设置默认的队列名称，如果一个消息不符合其他的队列就会放在默认队列里面，如果什么都不设置的话，数据都会发送到默认的队列中
    # CELERY_DEFAULT_QUEUE = "default"

    # ################################# Celery Standard Configuration ################################

    # ################################## User-Defined Configuration ##################################
    # Send Raw Message to `AMPQ` config
    CELERY_NATIVE_AMQP = "%s.hooks.amqp:Amqp" % __name__.rsplit(".", 1)[0]

    # Each task function can save separately execution results to a different backend (Redis, DB, filesystem etc.)
    CELERY_TASK_BACKEND_KEYWORD = "to_backend"
    CELERY_TASK_BACKENDS = {
        'redis': "redis://{user}:{password}@{host}:{port}/{db}".format(
            user=os.getenv("REDIS:USER"), password=os.getenv("REDIS:PASSWORD"),
            host=os.getenv("REDIS:HOST"), port=os.getenv("REDIS:PORT"), db=os.getenv("REDIS:DB0"),
        ),

        'djx_db': 'django-db',          # django_celery_results.backends:DatabaseBackend
        'djx_cache': 'django-cache',    # django_celery_results.backends:CacheBackend
        # 'file': 'file:///D:/data/celery/results',
    }

    CELERY_TASK_WATCHER = False  # Watch task to monitor
    # ################################## User-Defined Configuration ##################################


class QueueRouteConfig(object):
    """ Router config of RabbitMQ Queue """
    # User defined: CELERY_NOT_IMPORTS_TASKS => Tasks that do not need to be performed(useless task)
    if _APP_ENV == 'DEV':
        CELERY_NOT_IMPORTS_TASKS = []
    else:
        CELERY_NOT_IMPORTS_TASKS = [
            'test_concurrency_limit',
            'test_backend_default',
            'test_backend_prod_db',
            'test_backend_local_redis',
            'test_backend_prod_redis',
            'test_backend_prod_cache_redis',
            'test_backend_local_file',
        ]

    CELERY_IMPORTS = autodiscover_task_imports()

    # User defined: _expected_task_list => get fully expected celery tasks
    _expected_task_list = autodiscover_task_list(CELERY_IMPORTS, not_import_tasks=CELERY_NOT_IMPORTS_TASKS)

    CELERY_QUEUES = [
        Queue(
            name=task_item["task_name"] + "_q",  # task name as queue name
            exchange=Exchange(task_item["task_name"] + "_exc"),  # task name as exchange name
            routing_key=task_item["task_name"] + "_rk",  # task name as routing_key name
        )
        for task_item in _expected_task_list
    ]

    CELERY_ROUTES = {
        # The full path of the task(accurate to the function name): {queue_name, routing_key}
        # eg:
        #     {
        #         'myproject.apps.ding_talk.tasks.task_test_module.send_message': {
        #             'queue': 'send_message_q',
        #             'routing_key': 'send_message_rk',
        #         }
        #     }
        task_item["complete_name"]: {
            "queue": task_item["task_name"] + "_q",
            "routing_key": task_item["task_name"] + "_rk",
        }
        for task_item in _expected_task_list
    }


class CeleryConfig(BaseConfig, QueueRouteConfig):
    if _APP_ENV == 'DEV':
        BROKER_URL = f'redis://{os.getenv("REDIS:DEV:USER")}:{os.getenv("REDIS:DEV:PASSWORD")}' \
                     f'@{os.getenv("REDIS:DEV:HOST")}:{os.getenv("REDIS:DEV:PORT")}' \
                     f'/{os.getenv("REDIS:DEV:DB5")}'
    else:
        BROKER_URL = "amqp://{user}:{pwd}@{host}:{port}/{virtual_host}".format(
            user=os.getenv("RABBITMQ:USER"), pwd=os.getenv("RABBITMQ:PASSWORD"),
            host=os.getenv("RABBITMQ:HOST"), port=os.getenv("RABBITMQ:PORT"),
            virtual_host=os.getenv("RABBITMQ:VIRTUAL_HOST"),
        )

    # Periodic Tasks
    CELERYBEAT_SCHEDULE = {
        # Special task: Monitors whether a task continues to be executed
        "monitor_all_periodic_tasks": {
            'task': '%s.apps.ding_talk.tasks.task_periodic_ding_message.monitor_all_periodic_tasks' % __name__.split(".", 1)[0],
            'schedule': crontab(),  # Execute per minute
            'args': (),
            'kwargs': dict(),
        },

    }

