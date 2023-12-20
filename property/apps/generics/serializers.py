from rest_framework import serializers

from .util import get_model_class


class SerializerBase(serializers.ModelSerializer):
    def __new__(cls, *args, **kwargs):
        if not hasattr(cls, 'Meta'):
            raise ValueError("%s have not meta data class" % cls.__name__)

        request = kwargs['context']['request']
        if request.method == 'GET':
            model = request.query_params.get('model_name')
        else:
            model = request.data.get('model')

        Model = get_model_class(name=model)
        cls.Meta.model = Model
        cls.Meta.fields = Model.fields()

        return super().__new__(cls, *args, **kwargs)

    class Meta:
        model = None
        fields = []


class GenericSearchSerializer(SerializerBase):
    pass


class GenericDoOperationsSerializer(SerializerBase):
    def create(self, validated_data):
        return super().create(validated_data)

    def update(self, instance, validated_data):
        return super().update(instance, validated_data)

