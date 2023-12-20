import logging
import traceback
from collections import deque

from django.apps import apps
from django.utils.functional import cached_property
from django.core.exceptions import ImproperlyConfigured
from django.db import connections, models
from django.db.utils import DEFAULT_DB_ALIAS, DatabaseError, ProgrammingError
from django_redis import get_redis_connection


class MigrateDatabase:
    TABLE_IGNORES = [
        'django_migrations', 'django_session', 'django_admin_log', 'django_content_type',
        'auth_group', 'auth_group_permissions', 'auth_permission'
    ]

    def __init__(self, src_alias, dest_alias, chunk_size=None, ignore_tables=None):
        self._chunk_size = chunk_size or 2000
        self._src_alias = src_alias or DEFAULT_DB_ALIAS
        self._dest_alias = dest_alias or DEFAULT_DB_ALIAS

        if not self._src_alias and not self._dest_alias:
            raise ImproperlyConfigured("Src and Dest Database migration's config is empty.")

        if self._src_alias == DEFAULT_DB_ALIAS and self._dest_alias == DEFAULT_DB_ALIAS:
            raise ImproperlyConfigured("Src and Dest Database migration's config cannot be the same.")

        self.ping()

        ignore_tables = ignore_tables or []
        ignore_tables.extend(self.TABLE_IGNORES)
        self.cache_migrated_tables(ignore_tables, expired=True)

    @cached_property
    def logger(self):
        logger = logging.getLogger('db_migration')
        logger.setLevel(logging.INFO)
        ch = logging.StreamHandler()

        formatter = '%(asctime)s-%(name)s-%(filename)s-[line:%(lineno)d]-%(levelname)s-[日志信息]:-%(message)s'
        ch.setFormatter(logging.Formatter(formatter))

        ch.setLevel(logging.WARNING)
        logger.addHandler(ch)

        return logger

    def ping(self):
        # backend.DatabaseWrapper
        src_conn = connections[self._src_alias]
        dest_conn = connections[self._dest_alias]

        src_conn.ensure_connection()
        dest_conn.ensure_connection()

        if not src_conn.is_usable():
            raise DatabaseError('Database<src:%s> connection failure' % self._src_alias)

        if not connections[self._dest_alias].is_usable():
            raise DatabaseError('Database<dest:%s> connection failure' % self._dest_alias)

    def get_schema_sql(self, table, alias=None):
        """ 表存在的SQL """
        alias = alias or DEFAULT_DB_ALIAS
        assert alias in [self._src_alias, self._dest_alias], 'Database alias `%s` config is incorrect' % alias

        vendor = connections[alias].vendor

        if vendor in ['mysql', 'postgresql']:
            sql = "SELECT * FROM information_schema.TABLES WHERE table_name='%s'" % table
        elif vendor == 'oracle':
            pass
        elif vendor == 'sqlite':
            pass

        return sql

    def check_table(self, table_name, alias=None):
        cursor = connections[self._dest_alias].cursor()
        schema_sql = self.get_schema_sql(table_name, alias)
        cursor.execute(schema_sql)
        db_ret = cursor.fetchall()

        return bool(db_ret)

    def get_fields(self, model):
        return [f for f in model._meta.fields]

    def get_related_models(self, model):
        q = deque([model])
        related_models = []

        while q:
            model = q.popleft()

            if model not in related_models:
                related_models.append(model)

            for f in self.get_fields(model):
                # many2many: f.is_relation and f.many_to_many
                # one2many: f.is_relation and f.one_to_many
                # foreignKey: many2one
                if f.is_relation and f.many_to_one:
                    rel_model = f.related_model

                    # 无外循外键
                    if rel_model not in related_models:
                        q.append(rel_model)
                        related_models.append(rel_model)

        # 无任何关联表的模型
        for index, rel_model in enumerate(related_models[::]):
            if not any([f.is_relation and f.many_to_one for f in self.get_fields(rel_model)]):
                related_models.pop(index)
                related_models.append(rel_model)

        return related_models

    def get_queryset(self, model, start=None, alias=None):
        """
        :param model: ModelBase, ORM
        :param start: int | None, 上次queryset中最后一条记录的pk值
        :param alias: database's alias
        :return: Queryset
        """
        queryset = model._default_manager.using(alias or self._src_alias).order_by('pk').all()

        # 探测: {pk} 开始或中间可能不连续，需要每次传入最后一行记录pk参数 {start}
        #       如果不连续的间隔大于 {chunk_size}, 将导致取数失败, 所以必须探测
        if start is None:
            offset = 0
            first_obj = queryset.first()
        else:
            start += 1  # 上一次最后一条pk值(已存在)
            offset = start
            first_obj = queryset.filter(pk__gte=start).first()

        start = first_obj and first_obj.pk or offset
        end = start + self._chunk_size  # 以 chunk_size 为基准分片同步数据

        query = dict(pk__gte=start, pk__lt=end)
        log_args = (model.__name__, model._meta.db_table, query)
        self.logger.info("MigrateDatabase.migrate => <%s:%s> get_queryset -> query: %s", *log_args)

        return queryset.filter(**query).all()

    def cache_migrated_tables(self, tables=None, expired=False):
        redis = get_redis_connection()
        migrated_key = 'migrated_%s_to_%s' % (self._src_alias, self._dest_alias)

        cached_tables = redis.lrange(migrated_key, 0, -1) or []
        cached_tables = [tn.decode() if isinstance(tn, bytes) else tn for tn in cached_tables]

        if tables:
            tables = [tn for tn in set(tables or []) if tn not in cached_tables]
            tables and redis.lpush(migrated_key, *tables)

            if expired:
                redis.expire(migrated_key, 24 * 60 * 60)

            return

        return cached_tables

    def sync_model(self, model):
        model_name = model.__name__
        model_manager = model._default_manager  # equal to model.objects

        fields = [f.attname for f in self.get_fields(model)]
        dest_existed_ids = set(model_manager.using(self._dest_alias).values_list('pk', flat=True))

        src_queryset = self.get_queryset(model)

        while src_queryset.count() > 0:
            pk_start = getattr(src_queryset.last(), 'pk')
            object_kwargs_list = [
                {name: getattr(src_object, name, None) for name in fields}
                for src_object in src_queryset
                if src_object.pk not in dest_existed_ids
            ]

            try:
                bulk_objects = [model(**model_kwargs) for model_kwargs in object_kwargs_list]
                model_manager.using(self._dest_alias).bulk_create(bulk_objects)
            except DatabaseError as e:
                self.logger.error('MigrateDatabase.sync_model => bulk_create to error: %s', e)
                self.logger.error(traceback.format_exc())

                for model_kwargs in object_kwargs_list:
                    try:
                        model_manager.using(self._dest_alias).create(**model_kwargs)
                    except DatabaseError as e:
                        self.logger.info('MigrateDatabase.sync_model => create error: %s', e)
                        self.logger.error(traceback.format_exc())

            log_args = (model_name, model._meta.db_table, len(object_kwargs_list), self._dest_alias)
            self.logger.info("MigrateDatabase.migrate => <%s: %s> %s rows will migrate to `%s`", *log_args)

            src_queryset = self.get_queryset(model, start=pk_start)

    def migrate(self, models=None):
        app_models = apps.get_models()
        models = isinstance(models, list) and models or (models and [models] or [])

        for app_model in models or app_models:
            related_models = self.get_related_models(app_model)
            self.logger.info('MigrateDatabase.migrate => related_models: %s', related_models)

            for model in related_models[::-1]:
                model_name = model.__name__
                meta = model._meta
                db_table = meta.db_table
                migrated_tables = self.cache_migrated_tables()

                if db_table in migrated_tables:
                    self.logger.info("MigrateDatabase.migrate => %s<%s> has already ignored", model_name, db_table)
                    continue

                if not self.check_table(db_table, alias=self._dest_alias):
                    continue

                self.logger.info("MigrateDatabase.migrate => %s<%s> start to migrate now.", model_name, db_table)

                self.sync_model(model)
                self.reset_sql_sequence(db_table, pk_name=meta.pk.name)
                self.cache_migrated_tables([db_table])

    def reset_sql_sequence(self, table_name=None, pk_name=None):
        app_models = apps.get_models()
        conn = connections[self._dest_alias]
        vendor, cursor = conn.vendor, conn.cursor()

        if vendor != 'postgresql':
            raise ValueError("Dest database isn't PostGreSQL DB.")

        if table_name:
            seq_list = [(table_name, pk_name or 'id')]
        else:
            seq_list = [
                (model._meta.db_table, model._meta.pk.name)
                for model in app_models
                # django.db.models.fields.AutoField: pg serial sequence
                if isinstance(model._meta.pk, models.AutoField) and model._meta.managed
            ]

        for db_table, pk_name in seq_list:
            set_seq_sql = "SELECT SETVAL(pg_get_serial_sequence('%s','%s'), (SELECT MAX(%s) FROM %s) + 1);"
            params = (table_name, pk_name, pk_name, table_name)
            self.logger.info('MigrateDatabase.reset_sql_sequence => SQL: %s', set_seq_sql % params)

            try:
                cursor.execute(set_seq_sql % params)
                cursor.fetchone()
            except ProgrammingError:
                self.logger.error(traceback.format_exc())

