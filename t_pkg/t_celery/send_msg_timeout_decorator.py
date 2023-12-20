import time
import asyncio
import os, sys, django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.dev")
django.setup()

from property.apps.users.tasks.task_timeout_decorator import async_test_timeout_decorator
from property.apps.users.tasks.task_timeout_decorator import test_retry_message
from property.apps.users.tasks.task_timeout_decorator import async_send_raw_message


def send_msg():
    for i in range(1):
        # async_test_timeout_decorator.delay(i * 12)
        async_test_timeout_decorator.apply_async(args=(i * 12, ))


def test_mixed_nsg():
    for i in range(10000):
        async_test_timeout_decorator.delay(k=i)
        # test_retry_message.apply_async(kwargs=dict(k=i))
        async_send_raw_message.apply_async_raw(kwargs=dict(k=i))


if __name__ == "__main__":
    # send_msg()
    # test_retry_message.delay()

    test_mixed_nsg()
