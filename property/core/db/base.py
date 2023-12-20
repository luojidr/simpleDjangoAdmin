from copy import deepcopy
from datetime import date, datetime

from django.db import models
from django.db.models.base import ModelBase
from django.utils import timezone
from django.utils.functional import cached_property
from django.utils.deconstruct import deconstructible
from django.core.management.utils import get_random_string

from core.globals import local_user

__all__ = ('BaseModelMixin', )


@deconstructible
class AutoExecutor:
    def __init__(self):
        self._default = 'sys'

    def __call__(self, *args, **kwargs):
        try:
            login_user = local_user

            if login_user:
                return login_user.mobile

            return self._default
        except RuntimeError:
            return self._default


class BaseModelMixin(models.Model):
    """ 数据库 Model """

    creator = models.CharField(verbose_name="创建人", max_length=200, default=AutoExecutor())
    modifier = models.CharField(verbose_name="创建人", max_length=200, default=AutoExecutor())
    create_time = models.DateTimeField(verbose_name='创建时间', auto_now_add=True)
    update_time = models.DateTimeField(verbose_name='更新时间', auto_now=True)
    is_del = models.BooleanField(verbose_name='是否删除', default=False)

    class Meta:
        abstract = True

    def default(self, o):
        if isinstance(o, datetime):
            return o.strftime("%Y-%m-%d %H:%M:%S")

        if isinstance(o, date):
            return o.strftime("%Y-%m-%d")

        return o

    def save(self, *args, **kwargs):
        if not self.create_time:
            self.create_time = timezone.now()
        self.update_time = timezone.now()

        return super(BaseModelMixin, self).save(*args, **kwargs)

    def update_attrs(self, force_update=False, **kwargs):
        for attr, value in kwargs.items():
            self.__dict__[attr] = value

        if force_update:
            self.save()

        return self

    def to_dict(self, *extra, exclude=()):
        fields = list(set(self.fields() + list(extra)) - set(exclude))
        # model_dict = model_to_dict(self)
        return {_field: self.default(self.__dict__[_field]) for _field in fields}

    @classmethod
    def fields(cls, exclude=()):
        """ 获取非 BaseAbstractModel 的字段
         fields: opts = cls._meta | opts = instance._meta
            1: opts.get_fields()
            2: opts.fields
            3: opts.concrete_fields
            4: opts.private_fields, opts.many_to_many
         """
        fields = []
        exclude_fields = set(exclude)
        abc_fields = cls.abc_fields()

        for field in cls._meta.fields:
            field_name = field.attname

            if field_name in exclude_fields:
                continue

            if field_name not in abc_fields:
                fields.append(field_name)

        return fields

    @classmethod
    def get_fields(cls, exclude=()):
        return cls.fields(exclude=exclude)

    @classmethod
    def create_object(cls, force_insert=True, **kwargs):
        """ 创建对象 """
        model_fields = cls.fields()
        new_kwargs = {key: value for key, value in kwargs.items() if key in model_fields}

        if force_insert:
            obj = cls.objects.create(**new_kwargs)
        else:
            obj = cls(**new_kwargs)

        return obj

    @classmethod
    def abc_fields(cls):
        return [f.name for f in BaseModelMixin._meta.fields]

    @classmethod
    def get_sharding(cls, sharding_table):
        """ 水平分表(表结构相同)，适用于单表数据量太大切分到不同的表中 """
        return ShardingModel(shard_model_cls=cls).create_sharding_model(sharding_table)


class ShardingModel:
    """ ShardingModel support table horizontal partition """
    _shard_db_models = {}
    _base_shard_model_cls = None

    def __new__(cls,  *args, **kwargs):
        cls._base_shard_model_cls = kwargs.pop("shard_model_cls")
        return super().__new__(cls, *args, **kwargs)

    def create_sharding_model(self, sharding_table):
        class Meta:
            db_table = sharding_table
            ordering = ["-id"]

        class ShardMetaclass(ModelBase):
            def __new__(cls, name, bases, attrs):
                shard_model_cls = self._base_shard_model_cls
                base_model_name = shard_model_cls.__name__

                # 原字段可能存在缓存，导致查询时表名指向错误
                new_concrete_fields = {}
                for field in shard_model_cls._meta.concrete_fields:
                    dp_field = deepcopy(field)

                    for name in dir(dp_field.__class__):
                        val = getattr(dp_field.__class__, name, None)
                        if isinstance(val, cached_property) and hasattr(dp_field, name):
                            delattr(dp_field, name)

                    new_concrete_fields[field.name] = dp_field

                attrs.update({
                    '__module__': shard_model_cls.__module__,
                    '__doc__': 'Using %s table from %s Model' % (sharding_table, base_model_name),
                    'Meta': Meta
                }, **new_concrete_fields)

                model_name = sharding_table.title().replace("_", "") + "_Sharding_%s" % get_random_string(8)
                model_cls = super().__new__(cls, "%sModel" % model_name, shard_model_cls.__bases__, attrs)
                # model_meta = model_cls._meta
                # model_meta.db_table = sharding_table

                return model_cls

        class ProxyShardingModel(metaclass=ShardMetaclass):
            def __str__(self):
                model_name = self.__class__.__name__.split("_")[0]
                return '%s object (%s)' % (model_name, self.pk)

        model_class = self._shard_db_models.get(sharding_table)
        if model_class is not None:
            return model_class

        # 这种方法与原Model类一样，如果同时计算多个分表的数据，最终只有一个有效
        # model_class = self._base_shard_model_cls._meta.db_table = sharding_table

        # 每个id(model_class)不同，互不影响
        model_class = ProxyShardingModel
        self._shard_db_models[sharding_table] = model_class
        return model_class

    @staticmethod
    def get_relation_fields(fields):
        relation_fields = []

        for f in fields:
            # many2many
            if f.is_relation and f.many_to_many:
                pass

            # one2many
            if f.is_relation and f.one_to_many:
                pass

            # foreignKey: many2one
            if f.is_relation and f.many_to_one:
                pass
        return relation_fields

