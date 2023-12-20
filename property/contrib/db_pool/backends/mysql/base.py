# -*- coding: utf-8 -*-

from django.db.backends.mysql import base
from sqlalchemy.dialects.mysql.pymysql import MySQLDialect_pymysql
from ...core.mixins import PoolDatabaseWrapperMixin


class DatabaseWrapper(PoolDatabaseWrapperMixin, base.DatabaseWrapper):
    class SQLAlchemyDialect(MySQLDialect_pymysql):
        server_version_info = (0, )
