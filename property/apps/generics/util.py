import enum
import importlib
from functools import lru_cache

from django.apps import apps
from django.db.models import Q
from django.utils.functional import cached_property

from constant.base import EnumBase


def get_boolean_value(value):
    true_list = {'on', '1', 'true', 1, 'True'}
    false_list = {'off', '0', 'false', 0, 'False'}

    if value in true_list:
        return True
    elif value in false_list:
        return False


@lru_cache(maxsize=512)
def get_model_class(name):
    for model_cls in apps.get_models():
        model_name = model_cls._meta.model_name

        if model_name == name:
            return model_cls

    raise ValueError('Model<%s> not exist.' % name)


def get_serializer_class(model_name=None, model_cls=None):
    model_cls = model_cls or get_model_class(model_name)
    try:
        meta = model_cls._meta
        module = importlib.import_module(meta.app_config.name + '.serializers')
        serializer_name = '%sSerializer' % meta.object_name.rsplit('Model', 1)[0]

        if hasattr(module, serializer_name):
            return getattr(module, serializer_name)
    except (ModuleNotFoundError, AttributeError):
        pass


@enum.unique
class _QueryTypeEnum(EnumBase):
    FLOAT = ('float', 1)
    STRING = ('string', 2)
    INTEGER = ('integer', 3)
    DATE = ('date', 4)
    DATETIME = ('datetime', 5)
    BOOLEAN = ('boolean', 6)

    def type(self):
        return self.value[0]


class Query:
    fieldTypeEnum = _QueryTypeEnum

    def __init__(self, request):
        self._request = request

    @cached_property
    def model_fields(self):
        model_name = self._request.query_params.get('model_name')
        model_cls = get_model_class(name=model_name)
        return model_cls._meta.fields

    @property
    def keyword_query(self):
        q = Q()
        q.connector = 'OR'
        keyword = self._request.query_params.get('keyword')

        for field in self.model_fields:
            attname = field.attname

            if keyword and self._get_field_enum(field) == self.fieldTypeEnum.STRING:
                q.children.append(('%s__icontains' % attname, keyword))

        return q

    def _get_field_enum(self, field):
        internal_type = field.get_internal_type()

        if field.max_length is not None or internal_type == 'TextField':
            return self.fieldTypeEnum.STRING

        if internal_type == 'BooleanField':
            return self.fieldTypeEnum.BOOLEAN

        if internal_type == 'DateField':
            return self.fieldTypeEnum.DATE

        if internal_type == 'DateTimeField':
            return self.fieldTypeEnum.DATETIME

        if internal_type == 'FloatField':
            return self.fieldTypeEnum.FLOAT

        if self.fieldTypeEnum.INTEGER.type() in internal_type.lower() or internal_type == 'BigAutoField':
            return self.fieldTypeEnum.INTEGER

        raise TypeError('Not support field type<%s>.' % internal_type)

    @property
    def query(self):
        q = Q()
        query = self._request.query_params

        for field in self.model_fields:
            attname = field.attname
            value = query.get(attname)

            if not value:
                continue

            match self._get_field_enum(field):
                case self.fieldTypeEnum.STRING:
                    q.children.append(('%s__icontains' % attname, value))
                case self.fieldTypeEnum.BOOLEAN:
                    q.children.append((attname, get_boolean_value(value)))
                case self.fieldTypeEnum.FLOAT:
                    q.children.append((attname, float(value)))
                case self.fieldTypeEnum.INTEGER:
                    q.children.append((attname, int(value)))
                case self.fieldTypeEnum.DATE | self.fieldTypeEnum.DATETIME:
                    values = value if isinstance(value, (tuple, list)) else [value]
                    if len(values) == 1:
                        q.children.append((attname, values[0]))
                    else:
                        q.children.append(('%s__gt' % attname, values[0]))
                        q.children.append(('%s__lt' % attname, values[1]))

        return q | self.keyword_query

