import logging
import traceback

from django.core import signing
from django.conf import settings
from django.urls import reverse, NoReverseMatch, is_valid_path
from django.http import HttpResponseRedirect
from django.contrib.auth import get_user_model
from django.utils.functional import cached_property
from django.utils.deprecation import MiddlewareMixin

from rest_framework.request import Request
from rest_framework_simplejwt.settings import api_settings
from rest_framework_simplejwt.authentication import JWTAuthentication, AuthUser
from rest_framework_simplejwt.exceptions import AuthenticationFailed, TokenError, InvalidToken

from core import LocalContext
from utils.crypto import AESCipher

User = get_user_model()
logger = logging.getLogger('django')


class Authentication(JWTAuthentication):
    def authenticate(self, request: Request) -> AuthUser:
        auth_cookie_key = settings.AUTH_COOKIE_KEY
        token = request.COOKIES.get(auth_cookie_key)

        if token is None:
            raise InvalidToken(' Cookie: %s is empty.' % auth_cookie_key)

        plain_token = AESCipher(settings.AUTH_COOKIE_SALT).decrypt(token)
        validated_token = self.get_validated_token(raw_token=plain_token)

        return self.get_user(validated_token)


class AuthorizeMiddleware(MiddlewareMixin):
    """ 用户登录认证校验 """

    @cached_property
    def exempt_request_paths(self):
        attr = "_exempt_request_paths"
        view_names = [
            "login", "admin_password_reset",
        ]

        if attr not in self.__dict__:
            exempt_paths = ['/favicon.ico']

            for view_name in view_names:
                try:
                    exempt_paths.append(reverse(view_name))
                except NoReverseMatch:
                    pass

            try:
                exempt_paths.append(reverse("static", kwargs=dict(path="/")))
            except NoReverseMatch:
                pass

            self.__dict__[attr] = exempt_paths
            return exempt_paths

        return self.__dict__[attr]

    def _exempt_csrf_token(self, request):
        # Avoid error: rest_framework.exceptions.PermissionDenied:
        # CSRF Failed: CSRF token missing or incorrect. But anonymous user
        # There are ways to skip CSFF validation:
        #   (1): Set request.csrf_processing_done = True, Skip all request check
        #   (2): Set callback of view function or view class to callback.csrf_exempt = True, Skip all request check
        #   (3): Set request._dont_enforce_csrf_checks = True, Skip 'POST' request check

        request._dont_enforce_csrf_checks = True

    def process_request(self, request):
        path = request.path
        self._exempt_csrf_token(request)
        logger.info("Middleware: %s, process_request => path: %s", self.__class__.__name__, path)

        # if not is_valid_path(path):
        #     return HttpResponseRedirect(reverse("monitor_inner_404"))

        if any([path.startswith(prefix_path) for prefix_path in self.exempt_request_paths]):
            return

        # 如果设置 AUTHORIZATION 请求头，无需进行用户验证(由simplejwt进行鉴权)
        if request.META.get(api_settings.AUTH_HEADER_NAME):
            return

        try:
            request.user = Authentication().authenticate(request)
        except (AuthenticationFailed, TokenError, InvalidToken):
            logger.error(traceback.format_exc())
        except User.DoesNotExist:
            pass
        except (KeyError, TypeError):
            pass
        else:
            return

        return HttpResponseRedirect(reverse("login"))
