import os.path
import pathlib
import logging
from logging.handlers import RotatingFileHandler
from django.conf import settings

__all__ = ["dj_logger", "task_logger", "worker_logger", "sql_logger"]


class AppLogger(object):
    """ 日志logger需要自定义，复用django或celery的logger在测试或本地环境可行，
    但是在生产环境很大可能上不能打印日志
    from django.utils.log import request_logger
    from celery.utils.log import base_logger as celery_log
    """

    def __init__(self):
        self._app_name = settings.APP_NAME
        self._app_log_dir = settings.BASE_LOG_DIR.format(self._app_name)

        if not os.path.exists(self._app_log_dir):
            os.makedirs(self._app_log_dir)

    def _get_logger(self, name, max_bytes=100 * 1024 * 1024, backup_count=10, encoding="utf-8"):
        """ Deprecated """
        _logger = logging.getLogger(name)
        _logger.setLevel(logging.INFO)

        formatter = logging.Formatter("%s(asctime)s - %(name)s[line:%(lineno)d] - %(levelname)s] - : %(message)s")
        filename = "%s_%s.log" % (self._app_name, name.replace(".", "_"))
        log_filename = str(pathlib.Path(self._app_log_dir) / filename)

        rotating_handler = RotatingFileHandler(
            log_filename, maxBytes=max_bytes,
            backupCount=backup_count, encoding=encoding
        )
        rotating_handler.setFormatter(formatter)
        _logger.addHandler(rotating_handler)

        return _logger

    @property
    def dj_logger(self):
        """ Django log """
        return logging.getLogger('django')

    @property
    def task_logger(self):
        """ Task log to celery  """
        return logging.getLogger('celery.task')

    @property
    def worker_logger(self):
        """ Celery log """
        return logging.getLogger('celery.worker')

    @property
    def sql_logger(self):
        """ Database print sql log """
        return logging.getLogger('django.db.backends')


__logger = AppLogger()

dj_logger = __logger.dj_logger
task_logger = __logger.task_logger
worker_logger = __logger.worker_logger
sql_logger = __logger.sql_logger
