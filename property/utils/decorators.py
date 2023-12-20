from functools import wraps

from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

from retrying import retry


# (1): 仅对 django View 的Post 方法有csrf 豁免作用
#
# (2): 对 rest_framework APIView 的Post 方法没有有csrf 豁免作用
#   class ConfigApi(APIView):
#       @csrf_exempt
#       def post(self, request, *args, **kwargs):
#           pass
cls_csrf_exempt = method_decorator(csrf_exempt, name="dispatch")


def to_retry(f):
    return retry(stop_max_attempt_number=3)(f)
