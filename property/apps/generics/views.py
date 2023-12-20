import os.path

from django.apps import apps
from django.conf import settings
from django.views.generic.base import ContextMixin
from django.template.response import TemplateResponse
from django.template.exceptions import TemplateDoesNotExist

from rest_framework.views import APIView
from rest_framework.generics import mixins
from rest_framework.generics import ListAPIView
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response

from constant.action import ApiActionEnum

from .util import get_model_class, get_serializer_class, Query
from .serializers import GenericSearchSerializer, GenericDoOperationsSerializer


class GenericAppOptionsApi(APIView):
    def get(self, request, *args, **kwargs):
        apps_path = str(settings.APPS_DIR)
        app_list = [
            dict(id=key, label=app.verbose_name, value=app.name)
            for key, app in apps.app_configs.items()
            if app.path.startswith(apps_path)
        ]

        return Response(app_list)


class GenericModelOptionsApi(APIView):
    def get(self, request, *args, **kwargs):
        django_apps = apps.app_configs.values()
        app_name = request.query_params.get('app_name')
        required_apps = [app for app in django_apps if app_name == app.name] if app_name else django_apps

        models = [
            dict(
                id=model_name, value=model_name,
                label='%s:%s' % (app.models_module.__name__, model_cls._meta.object_name)
            )
            for app in required_apps
            for model_name, model_cls in app.models.items()
            if app.models_module
        ]

        return Response(models)


class GenericModelChoiceApi(APIView):
    def get(self, request, *args, **kwargs):
        model_name = self.request.query_params.get('model_name')
        Model = get_model_class(name=model_name)

        data = {
            attr.lower(): [dict(id=i, value=item[0], name=item[1]) for i, item in enumerate(vals, 1)]
            for attr, vals in Model.__dict__.items()
            if attr.isupper() and attr.endswith('CHOICES')
        }
        return Response(data=data)


class GenericTemplateAPI(ContextMixin, APIView):
    """ 通用获取Vue组件的html """
    TEMPLATE_DIR = "templates"

    def get_template_name(self):
        template_name = self.kwargs['template_name']
        possible_template_names = {
            template_name,
            template_name.replace('-', '_'),
            template_name.lower(),
            template_name.lower().replace('-', '_')
        }
        template_dir = str(settings.PROJECT_DIR / self.TEMPLATE_DIR)

        for root, dirs, files in os.walk(template_dir):
            for filename in files:
                name, _ = os.path.splitext(filename)

                if name in possible_template_names:
                    template_path = root[len(template_dir) + 1:]
                    template_name = os.sep.join([template_path, filename])

                    return template_name

        raise TemplateDoesNotExist('`%s` template not exist.' % template_name)

    def get(self, request, *args, **kwargs):
        template_response = TemplateResponse(
            request=self.request,
            template=[self.get_template_name()],
            context=self.get_context_data(**kwargs),
        )
        return Response(data=template_response.rendered_content)


class GenericDefaultFormAPI(APIView):
    def get(self, request, *args, **kwargs):
        model_name = request.query_params.get('model_name')
        Model = get_model_class(name=model_name)

        return Response(data={name: None for name in Model.fields()})


class BaseGenericApi(GenericAPIView):
    @property
    def Model(self):
        if self.request.method == 'GET':
            model_name = self.request.query_params.get('model_name')
        else:
            model_name = self.request.data.get('model')
        return get_model_class(name=model_name)

    def get_object(self):
        pk = self.request.data.get('id')
        return self.Model.objects.get(id=pk)

    def get_serializer_class(self):
        """ Defined its own serializer class """
        serializer_cls = get_serializer_class(model_cls=self.Model)
        if serializer_cls:
            return serializer_cls

        return super().get_serializer_class()


class ListGenericSearchAPI(ListAPIView, BaseGenericApi):
    serializer_class = GenericSearchSerializer

    def get_queryset(self):
        return self.Model.objects.filter(Query(self.request).query)


class GenericDoOperationsAPI(mixins.CreateModelMixin,
                             mixins.UpdateModelMixin,
                             BaseGenericApi):
    serializer_class = GenericDoOperationsSerializer

    def post(self, request, *args, **kwargs):
        action = request.data.pop('action', None)
        assert action in [e.action for e in ApiActionEnum.iterator()], "操作不合法"

        if action == ApiActionEnum.DELETE.action:
            self.get_object().update_attrs(force_update=True, is_del=True)
            return Response(data=None)

        # create, update
        return getattr(self, action)(request, *args, **kwargs, partial=True)


