import os.path
import json
import time
import traceback

import requests
from django.conf import settings

from config import celery_app
from property.utils.log import task_logger as logger


@celery_app.task
# def test_concurrency_limit(a, b=10, **kwargs):
def test_concurrency_limit():
    time.sleep(.1)
