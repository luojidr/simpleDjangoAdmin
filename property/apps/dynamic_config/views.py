from operator import itemgetter

from django.conf import settings
from django.utils.encoding import force_str
from django.views.decorators.csrf import csrf_exempt

from rest_framework.views import APIView
from rest_framework.response import Response

from constance import config as constance_config
from constance.backends.database.models import Constance
from constance.admin import ConstanceForm, get_values
from picklefield.fields import dbsafe_encode, get_default_protocol

from ...core.views import ListVueView


class TestConstanceConfigApi(APIView):
    def get(self, request, *args, **kwargs):
        data = {k: getattr(constance_config, k, None) for k in settings.CONSTANCE_CONFIG}

        return Response(data=data)


class ListDynamicConfigView(ListVueView):
    template_name = "dynamic-config/config.html"
    model = Constance

    def get_pagination_list(self):
        config_result = get_values()
        config_list = [dict(key=key, value=val) for key, val in config_result.items()]
        config_list.sort(key=itemgetter("key"))

        data_list = config_list[self.page_offset:self.page_limit + self.page_offset]
        return dict(list=data_list, total_count=len(config_result))


class UpdateConstanceConfigApi(APIView):
    form_cls = ConstanceForm

    @csrf_exempt
    def post(self, request, *args, **kwargs):
        """ 更新动态配置接口 """
        uniq_key = request.data.get("key")
        value = request.data.get("value")

        if not uniq_key or not value:
            raise ValueError("动态配置 key 或 value 错误")

        constance_val = force_str(dbsafe_encode(value, pickle_protocol=get_default_protocol()))

        constance_obj = Constance.objects.get(key=uniq_key)
        constance_obj.value = constance_val
        constance_obj.save()

        return Response(dict(
            message="OK", status=500,
            data=dict(key=uniq_key, value=getattr(constance_config, uniq_key, None))
        ))

