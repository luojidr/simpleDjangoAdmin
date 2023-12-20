import logging
import traceback

from django.urls import reverse
from django.conf import settings
from django.shortcuts import render
from django.utils import timezone
from django.views.generic import TemplateView, View
from django.http import HttpResponseRedirect
from django.contrib.auth import get_user_model
from django.db.models import Q

from rest_framework.generics import UpdateAPIView, ListAPIView

from rest_framework_simplejwt.settings import api_settings
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from . import forms, serializers
from utils.crypto import AESCipher
from middleware.authorize import Authentication

UserModel = get_user_model()
logger = logging.getLogger('django')
EXTRA_CONTENT = {
    'site_title': 'Simple管理后台',
    'site_header': 'Simple Admin'
}


class IndexView(TemplateView):
    template_name = "apps/index.html"
    extra_context = EXTRA_CONTENT


class LogoutView(View):
    def get(self, request):
        """ 登出 """
        response = HttpResponseRedirect(reverse("login"))
        response.delete_cookie(settings.CSRF_COOKIE_NAME)
        response.delete_cookie(settings.AUTH_COOKIE_KEY)

        return response


class LoginView(TemplateView):
    """ login view"""
    template_name = "apps/users/login.html"
    extra_context = EXTRA_CONTENT

    def post(self, request, *args, **kwargs):
        """ 登录认证 """
        form = forms.AuthLoginForm(request, request.POST)

        if form.is_valid():
            # user = form.get_user()
            serializer = TokenObtainPairSerializer()  # token_type: refresh
            token_data = serializer.validate(request.POST)
            token = token_data['access']
            cipher_token = AESCipher(settings.AUTH_COOKIE_SALT).encrypt(token)

            response = HttpResponseRedirect(reverse("index"))
            response.set_cookie(
                settings.AUTH_COOKIE_KEY,
                cipher_token,
                expires=timezone.datetime.now() + api_settings.ACCESS_TOKEN_LIFETIME,
                httponly=True
            )

            return response

        return render(request, self.template_name, context=dict(form=form))

    def get(self, request, *args, **kwargs):
        try:
            Authentication().authenticate(request)
        except Exception as e:
            logging.error(traceback.format_exc())
            logger.error('Must log in again, err: %s', str(e))

            context = self.get_context_data(**kwargs)
            response = self.render_to_response(context)
        else:
            response = HttpResponseRedirect(reverse("index"))

        return response


class ChangePasswordApi(UpdateAPIView):
    serializer_class = None

    def get_object(self):
        pass


class SearchUserApi(ListAPIView):
    serializer_class = serializers.SimpleUsersSerializer

    def get_queryset(self):
        keyword = self.request.query_params.get('keyword')
        queryset = self.serializer_class.Meta.model.objects.filter(is_del=False).all()

        if keyword:
            queryset = queryset.filter(Q(username__icontains=keyword) | Q(mobile__icontains=keyword)).all()

        return queryset

