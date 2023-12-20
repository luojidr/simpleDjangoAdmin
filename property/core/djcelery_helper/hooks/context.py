import re
import os
import time
import logging
import inspect
import traceback
from datetime import datetime
from urllib.parse import unquote, urlparse

from celery import Celery
from celery import version_info as celery_version
from celery.app import backends
from celery.app.task import Task
from celery.states import SUCCESS
from celery.utils.time import timezone
from celery.app.task import extract_exec_options
from kombu import Queue

from django.conf import settings

from .amqp import Amqp
from ..conf import CeleryConfig as Config
from ..utils.watcher import TaskWatcher

__all__ = ["ContextTask", "TaskSender"]

# Equivalent to `from myproject.libs.log import task_logger`
task_logger = logging.getLogger("celery.task")
worker_logger = logging.getLogger("celery.worker")

empty = object()


if celery_version < (5, 2, 7):
    task_logger.warning("Task to Celery version is %s, except 5.2.7", celery_version)
    worker_logger.warning("Worker to Celery version is %s, except 5.2.7", celery_version)


class BaseContextTask(Task):
    # Maximum frequency to retry
    DEFAULT_MAX_RETRIES = Task.max_retries

    # The keyword of the task function argument to try the maximum number of deliveries
    DEFAULT_RETRY_KEYWORD = "max_retry_cnt"

    # The task of consuming failure, delay time for the next extended execution
    DEFAULT_RETRY_COUNTDOWN = 1 * 60

    @property
    def backend(self):
        """ Default backend: self.app.backend (celery.app.base:Celery.backend)
         The execution results of tasks is stored to different backends, eg:
            celery.app.backends:BACKEND_ALIASES, django-db, django-cache, Redis, File etc.
        """
        native_signatures = self.get_native_task_signatures()
        backend_param = native_signatures.get(Config.CELERY_TASK_BACKEND_KEYWORD, {})
        to_backend = backend_param.get("default", empty)

        if to_backend and to_backend is not empty:
            # If task func has  its own `CELERY_TASK_BACKEND_KEYWORD`(default: 'to_backend') config,
            # the execution results of the task will be stored in the corresponding backend,
            # Instead of Celery default configuration backend(`CELERY_RESULT_BACKEND` config).
            if '://' in to_backend:
                backend_url = to_backend  # eg: redis://:@127.0.0.1:6379/0
                backend_name = to_backend.split('://')[0]
            else:
                backend_url, backend_name = None, to_backend

            task_backend_name = "CELERY_TASK_BACKEND_%s" % backend_name.replace('-', '_').upper()
            _backend = getattr(self, task_backend_name, None)

            if _backend:
                return _backend

            if backend_url is None:
                backend_url = Config.CELERY_TASK_BACKENDS.get(backend_name) or \
                              settings.CACHES.get(backend_name, {}).get('LOCATION')

            assert backend_url, "%s `to_backend` parameter not provide." % self.name

            backend_cls, url = backends.by_url(backend_url, self.app.loader)
            _backend = backend_cls(app=self.app, url=url)
            setattr(self, task_backend_name, _backend)

            return _backend

        else:
            # As with native celery, depends on `CELERY_RESULT_BACKEND` config
            backend = self._backend
            if backend is None:
                return self.app.backend

            return backend

    @backend.setter
    def backend(self, value):  # noqa
        self._backend = value
        worker_logger.info("ContextTask.backend -> Set value: %s", value)

    def log_info(self, log_kwargs, current_running_fun=None):
        if self is empty:
            worker_logger.info(">>>>>> ContextTask.log have't bond task instance !!!")

        log_kwargs.pop("self", None)
        log_kwargs["self_id"] = id(self)
        log_msg = log_kwargs.pop("log_msg", "")
        task_cls_name = self.app.task_cls.__name__

        log_msg = "{task_cls_name}.{current_running_fun} {log_msg} -> {running_fun_kwargs}".format(
            task_cls_name=task_cls_name, log_msg=log_msg,
            current_running_fun=current_running_fun, running_fun_kwargs=log_kwargs
        )
        worker_logger.info(log_msg)

    @classmethod
    def on_bound(cls, app):
        worker_logger.info("ContextTask.on_bound -> app: %s, cls<%s>: %s", app, id(cls), cls)

    def before_start(self, task_id, args, kwargs):
        """Handler called before the task starts(version 5.2).

        Returns:
            None: The return value of this handler is ignored.
        """
        kwargs['req_timestramp'] = time.time()
        return super().before_start(task_id, args, kwargs)

    def on_success(self, retval, task_id, args, kwargs):
        """ Success handler. Run by the worker if the task executes successfully """
        log_kwargs = dict(locals(), requestId=self.request.id, delivery_info=self.request.delivery_info)
        self.log_info(current_running_fun=inspect.stack()[0][3], log_kwargs=log_kwargs)

    def on_retry(self, exc, task_id, args, kwargs, einfo):
        """ Retry handler. This is run by the worker when the task is to be retried. """
        self.log_info(current_running_fun=inspect.stack()[0][3], log_kwargs=dict(locals()))
        super().on_retry(exc, task_id, args, kwargs, einfo)

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """ Error handler. This is run by the worker when the task fails. """
        self.log_info(current_running_fun=inspect.stack()[0][3], log_kwargs=dict(locals()))

        # The temporary monitoring task is abnormal
        if os.environ.get('CELERY_TASK_FAILURE_PUSH', True):
            task_name = self.name
            tz = timezone.get_timezone(self.app.conf.timezone)

            req_timestramp = kwargs.get('req_timestramp')
            run_time = datetime.now(tz=tz) if not req_timestramp else datetime.fromtimestamp(req_timestramp, tz=tz)

            TaskWatcher.send_dd_robot(
                title=f'Celery任务<{task_name.split(".")[-1]}>执行报错',
                task_name=f'{task_name}<task_id: {task_id}>',
                run_time=run_time.strftime('%Y-%m-%d %H:%M:%S'),
                error_msg=str(exc), error_detail=einfo.traceback,
            )

    def after_return(self, status, retval, task_id, args, kwargs, einfo):
        """ Handler called after the task returns.
            The status is not IGNORED, RETRY, REJECTED, after_return method will execute
        """
        log_kwargs = dict(locals(), requestId=self.request.id)
        current_running_fun = inspect.stack()[0][3]
        self.log_info(current_running_fun=current_running_fun, log_kwargs=log_kwargs)

        # self is bound task, the detail task instance is unique.
        # Each asynchronous task will have only one instance, because id(self) value is unique.
        # If message consumption fails, the message needs to be pushed back to the RabbitMQ queue
        # Note that: the best approach is not to ack messages if they fail and stay it in RabbitMQ.
        if status != SUCCESS:
            retry_log_kwargs = dict(Retry=True, args=args, kwargs=kwargs, task_id=task_id)
            self.log_info(current_running_fun=current_running_fun, log_kwargs=retry_log_kwargs)

            # The maximum number of attempts is 3 times by default
            # First method: Use the apply_async method to push the message into RabbitMQ again, It costs extra time.
            #        Each task function parameter must have the keyword parameter 'kwargs'. If the task_id is the same,
            #        only one record of the task execution result is stored the database. If the task_id is different,
            #        three records are stored.
            #
            # Second method: Use self.retry(....) for each specific task. , the message remains in RabbitMQ.
            #                Because the message has no ACK, the performance is better than `First method`,
            #                but it conflicts with `First method`
            if not self._check_task_bound_autoretry():
                default_max_retries = kwargs.get(self.DEFAULT_RETRY_KEYWORD, self.DEFAULT_MAX_RETRIES)
                current_max_retries = default_max_retries - 1

                max_retry_log_args = (self, id(self), current_max_retries)
                worker_logger.info("after_return.task: %s<%s>, current_max_retries:%s", *max_retry_log_args)

                if current_max_retries > 0:
                    kwargs[self.DEFAULT_RETRY_KEYWORD] = current_max_retries

                    # the `retries` parameter of `self.apply` method indicates the number of retry times,
                    # the same as Task.max_retries class property.
                    # self.apply_async(args, kwargs, task_id=task_id, countdown=self.DEFAULT_RETRY_COUNTDOWN)
                    self.retry(exc=einfo, countdown=self.DEFAULT_RETRY_COUNTDOWN)

        # Task Cost Time
        cost_log_kwargs = dict(
            task_id=task_id, status=status, retval=retval,
            cost_time=time.time() - kwargs['req_timestramp'],
        )
        self.log_info(current_running_fun=current_running_fun, log_kwargs=cost_log_kwargs)

        # Monitor for async, avoid to degrade performance
        if self.app.conf.CELERY_TASK_WATCHER:
            TaskWatcher().notice(request=self.request)

    def run(self, *args, **kwargs):
        """ The body of the task executed by workers."""
        self.log_info(current_running_fun=inspect.stack()[0][3], log_kwargs=dict(locals()))

        raise NotImplementedError('BaseJobTask must define the run method.')

    def __call__(self, *args, **kwargs):
        """ @Core: billiard.pool:Worker.workloop, 任务执行体: self.run 即@celery_app.task修饰的函数

        @任务执行: celery.app.trace:build_tracer 方法类的450行，然后跳转到本self.__call__
                  # 448   -*- TRACE -*-
                  # 449   try:
                  # 450       R = retval = fun(*args, **kwargs)
                  # 451       state = SUCCESS
                  # 452   except Reject as exc:

        @super().__call__: Task被修饰后的产物, celery.app.trace:_install_stack_protection, 733与734行, 即：
                           super().__call__ => __protected_call__

                  # def __protected_call__(self, *args, **kwargs):
                  #     stack = self.request_stack
                  #     req = stack.top
                  #     if req and not req._protected and \
                  #             len(stack) == 1 and not req.called_directly:
                  #         req._protected = 1
                  #         return self.run(*args, **kwargs)      # *** self.run 真正要执行的任务函数 ***
                  #     return orig(self, *args, **kwargs)
                  # BaseTask.__call__ = __protected_call__

        """
        retval = super().__call__(*args, **kwargs)

        task_id = request_id = self.request.id  # request_id is id of task
        log_kwargs = dict(
            log_msg="Task Call Finish", args=args, kwargs=kwargs, task_id=task_id,
            request_id=request_id, self=self, reqId=id(self.request), retval=retval,
        )
        self.log_info(current_running_fun=inspect.stack()[0][3], log_kwargs=log_kwargs)

        return retval

    def _check_task_bound_autoretry(self):
        """ Whether a retry mechanism is bound when the task function is defined, example:

            >>> @celery_app.task(bind=True)
            ... def test_retry_message(self, *args, **kwargs):
            ...     try:
            ...         pass
            ...     except Exception as e:
            ...         # Parameters in the retry method:
            ...         #    exc: Specify the exception to be thrown
            ...         #    throw: Whether to notify the worker to retry the task
            ...         #    eta: Specify the retry seconds or datetime
            ...         #    countdown: Delay seconds to execute
            ...         #    max_retries: Maximum retry times
            ...         raise self.retry(exc=e, countdown=10, max_retries=3)

            >>> @celery_app.task(max_retries=5)
            ... def test_retry_message(self, *args, **kwargs):
            ...     pass
        """
        has_autoretry = False
        task_retry_attr = "_TASK_AUTO_RETRY"
        auto_task_retry = getattr(self, task_retry_attr, has_autoretry)

        if auto_task_retry:
            return auto_task_retry

        source_code = inspect.getsource(self.run)

        # 1. Match `@celery_app.task(bind=True)` pattern
        retry_raise_pattern = r"^\s+?raise\s+.*?\.retry\(.*?\)"
        task_bind_regex = re.compile(r"@.*?\.task\(.*?bind=True.*?\).*?def\s+.*?\(.*?\):", re.S | re.M)
        task_bind_match = task_bind_regex.search(source_code)

        if task_bind_match:
            retry_raise_regex = re.compile(retry_raise_pattern, re.S | re.M)
            retry_raise_match = retry_raise_regex.search(source_code)
            has_autoretry = bool(retry_raise_match)

        else:
            # 2. Match `@celery_app.task(max_retries=5)` pattern
            task_retry_regex = re.compile(r"@.*?\.task\(.*?max_retries=\d.*?\).*?def\s+.*?\(.*?\):", re.S | re.M)
            task_retry_match = task_retry_regex.search(source_code)

            has_autoretry = bool(task_retry_match)

        setattr(self, task_retry_attr, has_autoretry)
        return has_autoretry

    def get_native_task_signatures(self):
        """ Arguments to the asynchronous task native function. """
        task_run = self.run  # be equal to self.__wrapped__
        params = inspect.signature(task_run).parameters
        native_signatures = dict(is_instance=self.is_bound_task())

        for name, param in params.items():
            kind = param.kind
            default = param.default
            native_signatures.setdefault(
                name,
                dict(
                    kind=kind.__str__(),
                    default=default is inspect.Parameter.empty and empty or default
                )
            )

        return native_signatures

    def is_bound_task(self):
        """
        >>> @app.task(bind=True, max_retries=10, rate_limit=25, ctx_name="djcelery", xx_job="dbs")
        ... def my_task(self, *args, **kwargs):
        ...     pass

        Explanation:
            bind: bool, whether to bind an instance of a task
                  If bind set to true, The first argument of task function is self, that access all the attributes
                  of the task instance. Not only the self could access all class attributes of `celery.app.task:Task`
                  (gg: rate_limit, time_limit,...), but also can access some custom attributes(eg: ctx_name, xx_job)

                 If bind set to false, The self only access the attributes of `Task` class.
        """
        return inspect.ismethod(self.run)


class ContextTask(BaseContextTask):
    """ Default config: celery.app.defaults """

    def delay(self, *args, **kwargs):
        """ Star argument version of :meth:`apply_async`.
        Does not support the extra options enabled by :meth:`apply_async`.
        """
        # Trace task log
        task_logger.info("ContextTask.delay <%s> send message ==>>> args:%s, kwargs: %s", self.name, args, kwargs)
        return self.apply_async(args, kwargs)

    def apply_async(self, args=None, kwargs=None, task_id=None, producer=None, link=None, link_error=None, shadow=None,
                    is_native=False, broker_url=None, queue_name=None, exchange_name=None, routing_key=None, **options):
        """ task_always_eager(reference: https://www.cnblogs.com/zh605929205/p/9866638.html):
            Default value：False
            If set to True, all tasks will be executed locally until they are returned.
            apply_async() and Task.delay() return an EagerResult instance that simulates
            the API and behavior of the AsyncResult instance, except that the results is calculated.

            That is, the task will be executed locally instead of being sent to the queue.
        """
        celery_app = self.app  # self.app and self._get_app() are the same instance of celery_app
        opts = dict(
            args=args, kwargs=kwargs, task_id=task_id, producer=producer,
            link=link, link_error=link_error, shadow=shadow, **options
        )
        q_opts = dict(queue_name=queue_name, exchange_name=exchange_name, routing_key=routing_key)

        # Trace task log
        task_logger.info("ContextTask.apply_async <%s> send task ==>>> opts: %s", self.name, opts)
        task_logger.info("ContextTask.apply_async <%s> send task ==>>> is_native: %s, q_opts: %s", self.name, is_native, q_opts)

        if is_native:
            sender = NativeTaskSender(
                broker_url=broker_url or celery_app.conf.broker_url,
                task_cls=celery_app.task_cls, app=celery_app,
                # config_source=celery_app._config_source,
            )
            return sender.send_raw_message(name=self.name, **dict(q_opts, **opts))

        try:
            return super().apply_async(**opts)
        except Exception as e:
            tz = timezone.get_timezone(celery_app.conf.timezone)
            TaskWatcher.send_dd_robot(
                title=f'Celery任务<{self.name.split(".")[-1]}>消息推送失败',
                task_name=f'{self.name}',
                run_time=datetime.now(tz=tz).strftime('%Y-%m-%d %H:%M:%S'),
                error_msg=traceback.format_exc()
            )

            raise e


class NativeTaskSender:
    """ Sending native message """

    def __init__(self, broker_url, task_cls=None, config_source=None, app=None):
        parse_result = urlparse(broker_url)
        virtual_host = unquote(parse_result.path.split("/")[-1])  # celery_app.connection().virtual_host
        self.pure_virtual_host = virtual_host.split("/")[-1]

        self.broker_url = broker_url
        self.task_cls = task_cls

        self.app = app
        self.config_source = config_source

    def _get_raw_app(self):
        sender_cls = self.__class__
        raw_apps = getattr(sender_cls, "_raw_apps", {})
        _raw_app = raw_apps.get(self.pure_virtual_host)

        if _raw_app:
            return _raw_app

        _raw_app = Celery(
            main="%sRawApp" % self.pure_virtual_host.title().replace('_', ''),
            amqp=getattr(Config, Config.CELERY_NATIVE_AMQP, Amqp),
            broker=self.broker_url, task_cls=self.task_cls, config_source=self.config_source
        )
        _raw_app.loader.config_from_object(self.config_source)

        # Attention timezone
        if self.app:
            timezone = self.app.conf.timezone
            enable_utc = self.app.conf.enable_utc
        else:
            timezone = settings.TIME_ZONE
            enable_utc = settings.USE_TZ  # TIME_ZONE is UTC, USE_TZ=True

        _raw_app.conf.timezone = timezone
        _raw_app.conf.enable_utc = enable_utc

        raw_apps[self.pure_virtual_host] = _raw_app
        sender_cls._raw_apps = raw_apps
        return _raw_app
    raw_app = property(_get_raw_app)

    def lookup_queue_opts(self, queue_name, exchange_name='', routing_key=''):
        q_opts = {}  # queue is necessary, routing_key could be missing
        raw_app = self.raw_app
        task_routes = raw_app.conf.task_routes or {}

        for completed_task_name, route in task_routes.items():
            q_name = route.get('queue')

            if q_name == queue_name:
                rk = route.get('routing_key')
                queues = [q for q in raw_app.conf.task_queues or () if q.name == queue_name]

                if queues:
                    target_q = queues[0]
                    q_opts['queue'] = target_q
                    rk = rk or target_q.routing_key
                    rk and q_opts.update(routing_key=rk)

                    break
        else:
            if not queue_name:
                raise TypeError('Send native message must provide `queue_name` parameters.')

            # exchange_name or routing_key could not provide
            q_opts['queue'] = Queue(name=queue_name, exchange=exchange_name, routing_key=routing_key)
            q_opts.update(routing_key=routing_key or None, exchange=exchange_name or None)

        return q_opts

    def send_raw_message(self, name,
                         queue_name=None, exchange_name=None, routing_key=None,
                         args=None, kwargs=None, task_id=None, producer=None,
                         ignore_result=False, priority=None, lang=None,
                         link=None, link_error=None, shadow=None, **options):
        """ Asynchronous sending raw message for more brokers """
        kwargs = kwargs or {}
        kwargs.setdefault("lang", lang)

        preopts = extract_exec_options(self)  # This self is not task
        options = dict(preopts, **options) if options else preopts

        options.setdefault('ignore_result', ignore_result)
        options.setdefault('priority', priority or 0)

        raw_app = self._get_raw_app()

        # Expands options, if queue_name does not exist, then the message is sent to the celery queue.
        if queue_name:
            queue_opts = self.lookup_queue_opts(queue_name, exchange_name, routing_key)
            options.update(**queue_opts)

        # Asynchronous message to send
        return raw_app.send_task(
            name, args, kwargs, task_id=task_id,
            producer=producer, link=link, link_error=link_error,
            result_cls=None, shadow=shadow, task_type=None, **options
        )


TaskSender = NativeTaskSender
