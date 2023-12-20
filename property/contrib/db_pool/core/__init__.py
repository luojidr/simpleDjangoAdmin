# -*- coding: utf-8 -*-

import threading
try:
    from django.utils.translation import ugettext_lazy as _
except ImportError:
    from django.utils.translation import gettext_lazy as _

from ..core.exceptions import PoolDoesNotExist


class ConnectionPool(dict):
    # the default parameters of pool
    pool_default_params = {
        'pre_ping': True,
        'echo': True,
        'timeout': None,
        'recycle': 60 * 60,
        'pool_size': 10,
        'max_overflow': 15,
    }

    def __new__(cls, *args, **kwargs):
        if not hasattr(cls, "_instance"):
            cls._instance = super(ConnectionPool, cls).__new__(cls, *args, **kwargs)

            # Important:
            # acquire this lock before modify pool_container
            cls._instance.lock = threading.Lock()

        return cls._instance

    def put(self, pool_name, pool):
        self[pool_name] = pool

    def get(self, pool_name):
        try:
            return self[pool_name]
        except KeyError:
            raise PoolDoesNotExist(_('No such pool: {pool_name}').format(pool_name=pool_name))


# the pool's container, for maintaining the pools
conn_pool = ConnectionPool()
