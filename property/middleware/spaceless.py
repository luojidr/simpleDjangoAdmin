import re
import json
from typing import Union

from django.conf import settings
from django.utils.deprecation import MiddlewareMixin
from django.utils.html import strip_spaces_between_tags


class SpacelessMiddleware(MiddlewareMixin):
    """  Remove Spaces between HTML tags with Spaceless """
    force_spaceless = False
    HTML_CONTENT_TYPE = 'text/html'

    SPACE_REGEX = re.compile(r' +?', re.M | re.S)
    LINE_BREAK_REGEX = re.compile(r'\n+?', re.M | re.S)
    COMMENT_REGEX = re.compile(r'<!--.*?-->', re.M | re.S)
    VUE_TEMPLATE_REGEX = re.compile(r'<template>.*?</template>', re.M | re.S)

    def can_spaceless(self, response):
        if self.is_html(response):
            return True

        if self.is_vue(response.content):
            return True

        return False

    def is_html(self, response):
        content_type = response.get('Content-Type')

        if not content_type:
            return False

        if self.HTML_CONTENT_TYPE in content_type:
            return True

        return bool(re.compile(rb"<!DOCTYPE").search(response.content))

    def is_vue(self, content: Union[bytes, str]):
        """ Mixed Content maybe have Html to Vue """
        if isinstance(content, bytes):
            content = content.decode()

        return bool(self.VUE_TEMPLATE_REGEX.search(content))

    def clean_whitespaces(self, content: Union[bytes, str]):
        if isinstance(content, bytes):
            content = content.decode()

        content = strip_spaces_between_tags(content.strip())        # remove HTML spaces between tags
        content = self.COMMENT_REGEX.sub("", content)               # remove HTML comment, like, eg <!--...-->
        content = self.SPACE_REGEX.sub(" ", content)                # remove HTML verbose spaces

        repl = "" if self.is_vue(content) else r'\n'
        content = self.LINE_BREAK_REGEX.sub(repl, content)  # replace linebreak

        return content

    def process_response(self, request, response):
        if response.status_code == 200 and self.can_spaceless(response):
            response.content = self.clean_whitespaces(response.content)

        return response
