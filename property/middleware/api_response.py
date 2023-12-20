import re
import json
import logging
import traceback

from django.urls import reverse
from django.utils.deprecation import MiddlewareMixin
from django.template.response import TemplateResponse
from django.http.response import HttpResponseBase
from django.http import JsonResponse, StreamingHttpResponse, HttpResponseRedirect

from rest_framework import status
from rest_framework.response import Response

from constant.status import StatusEnum

logger = logging.getLogger('django')


class ApiResponseMiddleware(MiddlewareMixin):
    def process_exception(self, request, exc):
        """ 处理Django异常, DRF框架有自己的异常处理钩子 """
        logger.info("%s.process_exception => request: %s, exc: %s", self.__class__.__name__, request, exc)
        logger.error(traceback.format_exc())

        code = getattr(exc, "code", 500)
        exc_args = getattr(exc, "args", ())

        if len(exc_args) > 1:
            code, errmsg = exc_args[0], exc_args[1]
        else:
            errmsg = exc_args[0] if exc_args else getattr(exc, "msg", str(exc))

        data = dict(code=code, errmsg=errmsg)

        # 基本的异常处理, 默认path为 /api/ 或 视图类有API的认为是接口API
        if request.path.startswith("/api/"):
            return JsonResponse(data=data, status=500)

    def process_request(self, request):
        pass

    def process_response(self, request, response):
        path = request.path
        logger.info("%s.process_response => Request: %s, Response:%s", self.__class__.__name__, request, response)

        # 微信
        # if path.startswith(reverse("wechat_robot")):
        #     return response

        # Django-Debug-Toolbar
        if path.startswith("/__debug__/"):
            return response

        # 直接返回response:
        if getattr(response, "_raw_response", False):
            return response

        # 附件
        if response.get("Content-Disposition"):
            return response

        # 静态文件
        if path.startswith('/static/') or any([path.endswith(ext) for ext in ['.css', '.less', 'sass', '.js']]):
            return response

        if any([
            not path.startswith('/api/') and isinstance(response, cls)
            for cls in [StreamingHttpResponse, TemplateResponse, HttpResponseRedirect, HttpResponseBase]
        ]):
            return response

        try:
            content = response.content
            is_json = 'application/json' in response.get('Content-Type')

            # 网页、模板、重定向 直接返回
            if not is_json and re.compile(rb"<!DOCTYPE").search(content):
                return response

            raw_data = getattr(response, "data", None) or json.loads(content)
        except (TypeError, AttributeError, json.JSONDecodeError):
            raw_data = {}

        data = dict(code=StatusEnum.OK.code, errmsg=StatusEnum.OK.msg, data=None)

        if status.is_success(response.status_code):
            data.update(data=raw_data)
        else:
            code = raw_data.pop("code", None) or response.status_code
            data.update(code=code, errmsg=str(raw_data.pop("message", "")))

        if not isinstance(response, Response):
            # Django.http.response.JsonResponse
            response = JsonResponse(data=data)
        else:
            # rest_framework 标准响应
            response.data = data
            response._is_rendered = False

        if hasattr(response, "render"):
            response.render()

        return response
