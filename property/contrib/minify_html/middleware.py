import re
import json

from django.conf import settings
from django.utils.deprecation import MiddlewareMixin

from .minify import html_minify


class MarkRequestMiddleware(MiddlewareMixin):
    def process_request(self, request):
        request._hit_htmlmin = True


class HtmlMinifyMiddleware(MiddlewareMixin):
    HTML_REGEX = re.compile(r'<template>.*?</template>', re.M | re.S)

    def _is_hybrid(self, response):
        """ A hybrid of html and json """
        # Mixed Content maybe have Html to Vue
        try:
            if self.HTML_REGEX.search(response.content.decode()):
                data = json.loads(response.content)
                if 'html' in data:
                    return True
        except json.JSONDecodeError:
            pass

        return False

    def _html_minify_hybrid(self, response, ignore_comments=True, parser=None):
        data = json.loads(response.content)
        mini_html = html_minify(data['html'], ignore_comments=ignore_comments, parser=parser)
        data['html'] = mini_html

        return json.dumps(data)

    def can_minify_response(self, request, response):
        try:
            req_ok = request._hit_htmlmin
        except AttributeError:
            return False

        if hasattr(settings, 'EXCLUDE_FROM_MINIFYING'):
            for url_pattern in settings.EXCLUDE_FROM_MINIFYING:
                regex = re.compile(url_pattern)
                if regex.match(request.path.lstrip('/')):
                    req_ok = False
                    break

        resp_ok = 'text/html' in response.get('Content-Type', '')
        if hasattr(response, 'minify_response'):
            resp_ok = resp_ok and response.minify_response

        return req_ok and resp_ok

    def process_response(self, request, response):
        minify = getattr(settings, "HTML_MINIFY", not settings.DEBUG)
        keep_comments = getattr(settings, 'KEEP_COMMENTS_ON_MINIFYING', False)
        parser = getattr(settings, 'HTML_MIN_PARSER', 'html5lib')

        if minify:
            if self.can_minify_response(request, response):
                content = html_minify(response.content, ignore_comments=not keep_comments, parser=parser)
            elif self._is_hybrid(response):
                # Issue: 子组件的自组件无法正产展示
                content = self._html_minify_hybrid(response, ignore_comments=not keep_comments, parser=parser)
            else:
                content = response.content

            response.content = content
            response['Content-Length'] = len(content)

        return response
