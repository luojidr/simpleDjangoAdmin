import time
import logging

import timeout_decorator
from config.celery import app as celery_app

logger = logging.getLogger("celery.task")


@celery_app.task
# @timeout_decorator.timeout(0.2)
def async_test_timeout_decorator(task_to_backend="default",**kwargs):
    time.sleep(0.1)
    # raise ValueError("DDDD: %s" % a)
    return "test_timeout"


@celery_app.task
def async_send_raw_message(task_to_backend=None, **kwargs):
    # 重试机制???
    time.sleep(0.1)
    return "raw_msg"


@celery_app.task(bind=True)
def test_retry_message(self, task_to_backend="file", *args, **kwargs):
    try:
        time.sleep(0.1)
        return "celery_msg"
    except Exception as e:
        """
        retry的参数可以有：
            exc：指定抛出的异常
            throw：重试时是否通知worker是重试任务
            eta：指定重试的时间／日期
            countdown：在多久之后重试（每多少秒重试一次）
            max_retries：最大重试次数
        """
        raise self.retry(exc=e, countdown=1, max_retries=3)
