import os
import sys
import json
import logging
import traceback
from datetime import datetime, timedelta

import requests

from kombu import Exchange, Queue
from celery import current_app
from celery.worker.request import Request
from django.conf import settings

from .cached_property import cached_property


class WatcherConfig:
    TASK_TIME_LIMIT = 60    # 任务执行的最大运行时间


class TaskWatcher:
    _task = None
    finalize_conf = False

    def __new__(cls, *args, **kwargs):
        if not hasattr(cls, "_instance"):
            cls._instance = super(TaskWatcher, cls).__new__(cls)

            cls._instance.loading_conf()
            cls._instance.registry_task()

        return cls._instance

    def loading_conf(self):
        if not self.finalize_conf:
            pass

        self.finalize_conf = True

    def registry_task(self):
        name = self.do_watch.__name__
        default_qname = name + '_q'
        default_exchange = name + '_exc'
        default_routing_key = name + '_rk'

        task_queues = current_app.conf.task_queues or []
        task_routes = current_app.conf.task_routes or {}
        self._task = current_app.task(self.do_watch, ignore_result=True)

        # task_queues, eg：
        #     {'cpubound': {'exchange': 'cpubound', 'routing_key': 'cpubound'},}
        # Or
        #     [Queue('default',    routing_key='task.#'),]
        for q in task_queues:
            qname = q.name if isinstance(q, Queue) else q

            if qname == default_qname:
                break
        else:
            q = Queue(default_qname, default_exchange, default_routing_key)
            if task_queues:
                current_app.conf.task_queues.append(q)
            else:
                current_app.conf.task_queues = [q]

        for completed_task_name, route in task_routes.items():
            q_name = route.get('queue')

            if self._task.name == completed_task_name and q_name == default_qname:
                break
        else:
            route = {self._task.name: {'queue': default_qname, 'routing_key': default_routing_key}}
            current_app.conf.task_routes.update(**route)

        if self._task.name not in current_app.tasks:
            current_app.tasks.register(self._task)

    @cached_property
    def push(self):
        try:
            from easypush import easypush

            return easypush
        except ImportError:
            raise ImportError('No module easypush, install `django-easypush` first!')

    @staticmethod
    def do_watch(request, **kwargs):
        """ watch task """
        # TaskWatcher().push.async_send(
        #     msgtype='oa',
        #     body_kwargs=dict(
        #         title="监控测试", media_id='@lADPDfmVbgbLbZ_NAX_NA4Q', content="Test123",
        #         message_url='https://cuth.com/exerland/questionnaireDetail?questionnaire_id=23',
        #         pc_message_url='https://cuth.com/exerland/questionnaireDetail?questionnaire_id=23',
        #     ),
        #     userid_list=['manager8174']
        # )

    def notice(self, request=None):
        """
        :param request: task request
        """
        if isinstance(request, Request) and self._task.name != request.task:
            return self._task.delay(request=None)

    @staticmethod
    def send_dd_robot(
            title, task_name,
            app_name=None, run_time=None, error_msg=None,
            error_detail=None, push_id=1000, error_url=None
    ):
        logging.warning('TaskWatcher.send_dd_robot: => vars: %s', vars())

        headers = {'Content-Type': 'application/json'}
        api_path = '{host}/{api}'.format(host=settings.CIRCLE_SERVICE_HOST, api=settings.CIRCLE_MONITOR_API)

        try:
            etype, value, tb = sys.exc_info()
            data = dict(
                push_id=push_id, title=title,
                project_name=app_name or os.environ.get('APP_NAME') or settings.APP_NAME,
                task_name=task_name, error_url=error_url,
                run_time=run_time or (datetime.now() + timedelta(hours=8)).strftime('%Y-%m-%d %H:%M:%S'),
                error_time=(datetime.now() + timedelta(hours=8)).strftime('%Y-%m-%d %H:%M:%S'),
                error_msg=error_msg or str(value),
                error_detail=error_detail or traceback.format_exc(),

                webhook_url=settings.DD_CUSTOM_ROBOT_WEBHOOK_URL,
                access_token=settings.DD_CUSTOM_ROBOT_WEBHOOK_ACCESS_TOKEN,
                secret=settings.DD_CUSTOM_ROBOT_WEBHOOK_SECRET,
            )

            requests.post(api_path, data=json.dumps(data), headers=headers)
        except Exception as e:
            logging.error(traceback.format_exc())

