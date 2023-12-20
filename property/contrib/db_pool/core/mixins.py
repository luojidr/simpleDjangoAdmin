# -*- coding: utf-8 -*-

from copy import deepcopy
from sqlalchemy import pool
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
try:
    from django.utils.translation import ugettext_lazy as _
except ImportError:
    from django.utils.translation import gettext_lazy as _

from . import conn_pool

import logging
logger = logging.getLogger("django")


class PoolDatabaseWrapperMixin(object):
    def get_new_connection(self, conn_params):
        """
        override django.db.backends.<database>.base.DatabaseWrapper.get_new_connection to
        change the default behavior of getting new connection to database, we maintain
        conn_pool who contains the connection pool of each database here
        when django call this method to get new connection, we check whether there exists
        the pool of this database(self.alias)
        if the target pool doesn't exist, we will create one
        then grab one connection from the pool and return it to django
        :return:
        """
        with conn_pool.lock:
            # acquire the lock, check whether there exists the pool of current database
            # note: the value of self.alias is the name of current database, one of setting.DATABASES
            if self.alias not in conn_pool:
                # self.alias's pool doesn't exist, time to create it

                # make a copy of default parameters
                pool_params = deepcopy(conn_pool.pool_default_params)

                # parse parameters of current database from self.settings_dict
                pool_setting = {
                    # transform the keys in POOL_OPTIONS to upper case
                    # to fit sqlalchemy.pool.QueuePool's arguments requirement
                    key.lower(): value
                    # traverse POOL_OPTIONS to get arguments
                    for key, value in
                    # self.settings_dict was created by Django
                    # is the connection parameters of self.alias
                    self.settings_dict.get('POOL_OPTIONS', {}).items()
                    # There are some limits of self.alias's pool's option(POOL_OPTIONS):
                    # the keys in POOL_OPTIONS must be capitalised
                    # and the keys's lowercase must be in conn_pool.pool_default_params
                    if key == key.upper() and key.lower() in conn_pool.pool_default_params
                }

                # replace pool_params's items with pool_setting's items
                # to import custom parameters
                pool_params.update(**pool_setting)

                # method of connection initiation defined by django
                # django.db.backends.<database>.base.DatabaseWrapper
                django_get_new_connection = super(PoolDatabaseWrapperMixin, self).get_new_connection

                # method of connection initiation defined by
                # dj_db_conn_pool.backends.<database>.base.DatabaseWrapper
                get_new_connection = getattr(self, '_get_new_connection', django_get_new_connection)

                # now we have all parameters of self.alias
                # create self.alias's pool
                alias_pool = pool.QueuePool(
                    # super().get_new_connection was defined by
                    # db_pool.backends.<database>.base.DatabaseWrapper or
                    # django.db.backends.<database>.base.DatabaseWrapper
                    # the method of connection initiation
                    lambda: get_new_connection(conn_params),
                    # SQLAlchemy use the dialect to maintain the pool
                    dialect=self.SQLAlchemyDialect(dbapi=self.Database),
                    # parameters of self.alias
                    **pool_params
                )

                logger.info(_("%s's pool has been created, parameter: %s"), self.alias, pool_params)

                # pool has been created
                # put into conn_pool for reusing
                conn_pool.put(self.alias, alias_pool)

        # get self.alias's pool from conn_pool
        db_pool = conn_pool.get(self.alias)
        # get one connection from the pool
        conn = db_pool.connect()
        # logger.info(_("got %s's connection from its pool"), self.alias)
        return conn

    def close(self, *args, **kwargs):
        # logger.info(_("release %s's connection to its pool"), self.alias)
        return super(PoolDatabaseWrapperMixin, self).close(*args, **kwargs)
