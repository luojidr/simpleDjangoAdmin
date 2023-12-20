# -*- coding: utf-8 -*-

import logging
from functools import partial

from django.conf import settings
from django.db.backends.postgresql import base

from sqlalchemy import event
from sqlalchemy.pool import manage, QueuePool
from sqlalchemy.dialects.postgresql.psycopg2 import PGDialect_psycopg2
from psycopg2 import InterfaceError, ProgrammingError, OperationalError

try:
    # Django >= 1.9
    from django.db.backends.postgresql.base import *
    from django.db.backends.postgresql.base import DatabaseWrapper as Psycopg2DatabaseWrapper
    from django.db.backends.postgresql.creation import DatabaseCreation as Psycopg2DatabaseCreation
except ImportError:
    from django.db.backends.postgresql_psycopg2.base import *
    from django.db.backends.postgresql_psycopg2.base import DatabaseWrapper as Psycopg2DatabaseWrapper
    from django.db.backends.postgresql_psycopg2.creation import DatabaseCreation as Psycopg2DatabaseCreation


from ...core.mixins import PoolDatabaseWrapperMixin

log = logging.getLogger('django')


def _log(message, *args):
    log.debug(message, *args)


# Only hook up the listeners if we are in debug mode.
if settings.DEBUG:
    event.listen(QueuePool, 'checkout', partial(_log, 'retrieved from pool'))
    event.listen(QueuePool, 'checkin', partial(_log, 'returned to pool'))
    event.listen(QueuePool, 'connect', partial(_log, 'new connection'))


def is_disconnect(e, connection, cursor):
    """
    Connection state check from SQLAlchemy:
    https://bitbucket.org/sqlalchemy/sqlalchemy/src/tip/lib/sqlalchemy/dialects/postgresql/psycopg2.py
    """
    if isinstance(e, OperationalError):
        # these error messages from libpq: interfaces/libpq/fe-misc.c.
        # TODO: these are sent through gettext in libpq and we can't
        # check within other locales - consider using connection.closed
        return 'terminating connection' in str(e) or \
               'closed the connection' in str(e) or \
               'connection not open' in str(e) or \
               'could not receive data from server' in str(e)
    elif isinstance(e, InterfaceError):
        # psycopg2 client errors, psycopg2/conenction.h, psycopg2/cursor.h
        return 'connection already closed' in str(e) or \
               'cursor already closed' in str(e)
    elif isinstance(e, ProgrammingError):
        # not sure where this path is originally from, it may
        # be obsolete.   It really says "losed", not "closed".
        return "closed the connection unexpectedly" in str(e)
    else:
        return False


class DeprecatedDatabaseWrapper(PoolDatabaseWrapperMixin, base.DatabaseWrapper):
    """
    Reference: https://github.com/altairbow/django-db-connection-pool
    Issues: 查询没有问题, insert + update 不起作用
    """

    class SQLAlchemyDialect(PGDialect_psycopg2):
        pass


class DatabaseCreation(Psycopg2DatabaseCreation):
    def destroy_test_db(self, *args, **kw):
        """Ensure connection pool is disposed before trying to drop database."""
        self.connection._dispose()
        super(DatabaseCreation, self).destroy_test_db(*args, **kw)


class DatabaseWrapper(Psycopg2DatabaseWrapper):
    """ SQLAlchemy FTW.
    Reference: https://github.com/heroku-python/django-postgrespool
    """

    POOL_SETTINGS = {
        'pre_ping': True,
        'echo': True,
        'timeout': None,
        'recycle': 60 * 60,
        'pool_size': 10,
        'max_overflow': 15,
    }

    def __init__(self, *args, **kwargs):
        super(DatabaseWrapper, self).__init__(*args, **kwargs)
        self.creation = DatabaseCreation(self)

    @property
    def db_pool(self):
        pool_setting = {}
        pool_options = self.settings_dict.get('POOL_OPTIONS', {})

        for key, value in self.POOL_SETTINGS.items():
            if key.upper() in pool_options:
                pool_setting.setdefault(key.lower(), pool_options[key.upper()])
            else:
                pool_setting.setdefault(key.lower(), value)

        if hasattr(self, "_db_pool"):
            pool = getattr(self, "_db_pool")
        else:
            pool = manage(Database, **pool_setting)
            setattr(self, "_db_pool", pool)

        log.info("contrib.db_pool.backends.postgresql.base.DatabaseWrapper <db_pool>: %s", pool)
        return pool

    def _commit(self):
        log.info("DatabaseWrapper._commit -> connection: %s, is_usable: %s", self.connection, self.is_usable)

        if self.connection is not None and self.is_usable():
            with self.wrap_database_errors:
                return self.connection.commit()

    def _rollback(self):
        if self.connection is not None and self.is_usable():
            with self.wrap_database_errors:
                return self.connection.rollback()

    def _dispose(self):
        """Dispose of the pool for this instance, closing all connections."""
        self.close()
        # _DBProxy.dispose doesn't actually call dispose on the pool
        conn_params = self.get_connection_params()
        key = self.db_pool._serialize(**conn_params)
        try:
            pool = self.db_pool.pools[key]
        except KeyError:
            log.info("DatabaseWrapper._dispose err")
        else:
            pool.dispose()
            del self.db_pool.pools[key]

    def is_usable(self):
        # https://github.com/kennethreitz/django-postgrespool/issues/24
        return not self.connection.closed


