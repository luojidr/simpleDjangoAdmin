# -*- coding: utf-8 -*-

from django.db.backends.oracle import base
from cx_Oracle import DatabaseError
from sqlalchemy.dialects.oracle.cx_oracle import OracleDialect
from ...core.mixins import PoolDatabaseWrapperMixin


class DatabaseWrapper(PoolDatabaseWrapperMixin, base.DatabaseWrapper):
    class SQLAlchemyDialect(OracleDialect):
        def do_ping(self, dbapi_connection):
            try:
                return super(OracleDialect, self).do_ping(dbapi_connection)
            except DatabaseError:
                return False
