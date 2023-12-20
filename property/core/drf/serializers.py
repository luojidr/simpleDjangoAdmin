import logging

from django.conf import settings
from django.core.cache import cache
from django.contrib.auth import authenticate, get_user_model
from django.utils.translation import ugettext as _
from rest_framework import serializers

from rest_framework_jwt.serializers import Serializer
from rest_framework_jwt.settings import api_settings
from rest_framework_jwt.compat import get_username_field

from fosun_circle.contrib.ding_talk.uuc import UUCUser
from fosun_circle.apps.users.models import CircleUsersModel


UserModel = get_user_model()
logger = logging.getLogger("django")

jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER
jwt_decode_handler = api_settings.JWT_DECODE_HANDLER
jwt_get_username_from_payload = api_settings.JWT_PAYLOAD_GET_USERNAME_HANDLER


class UsersSerializer(serializers.ModelSerializer):
    """ Necessary user information after login """
    username = serializers.CharField(max_length=150, read_only=True, default="", help_text="用户名")
    avatar = serializers.CharField(max_length=500, read_only=True, default="", help_text="用户头像")
    state_code = serializers.CharField(max_length=10, read_only=True, default="+86", help_text="国家码")
    phone_number = serializers.CharField(max_length=20, read_only=True, default="", help_text="电话号码")
    position_chz = serializers.CharField(max_length=200, read_only=True, default="", help_text="职位中文名")

    class Meta:
        model = CircleUsersModel
        fields = ("username", "avatar", "state_code", "phone_number", "position_chz")


class JwtTokenSerializer(Serializer):
    """
    Serializer class used to validate a username and sms_code.

    'username' is identified by the custom UserModel.USERNAME_FIELD.

    Returns a JSON Web Token that can be used to authenticate later calls.
    """
    def __init__(self, *args, **kwargs):
        """
        Dynamically add the USERNAME_FIELD to self.fields.
        """
        super(JwtTokenSerializer, self).__init__(*args, **kwargs)

        self.fields[self.username_field] = serializers.CharField()

        # 这里改动过
        self.fields[self.password_field] = serializers.CharField()

    @property
    def username_field(self):
        return get_username_field()

    @property
    def password_field(self):
        password_field = api_settings.user_settings.get("JWT_PASSWORD_FIELD", "password")
        logger.info("JWT_AUTH Settings `JWT_PASSWORD_FIELD`: %s", password_field)

        return password_field

    def validate(self, attrs):
        credentials = {
            self.username_field: attrs.get(self.username_field),

            # 不需要密码，使用验证码, 设置默认密码
            "password":  UserModel.DEFAULT_PASSWORD

        }

        if all(credentials.values()):
            sms_code = attrs.get(self.password_field)
            cache_key = "sms_code:%s" % attrs.get(self.username_field)
            cache_sms_code = cache.get(cache_key)

            if sms_code != settings.UNIVERSAL_SMS_CODE and cache_sms_code != sms_code:
                raise serializers.ValidationError("验证码错误")

            user = authenticate(**credentials)
            if user is None:
                user = UUCUser(attrs.get(self.username_field)).create_uuc_user()

            if user:
                if not user.is_active:
                    msg = _('User account is disabled.')
                    raise serializers.ValidationError(msg)

                payload = jwt_payload_handler(user)

                return {
                    'token': jwt_encode_handler(payload),
                    'user': user
                }
            else:
                msg = _('Unable to log in with provided credentials.')
                raise serializers.ValidationError(msg)
        else:
            msg = _('Must include "{username_field}" and "password".')
            msg = msg.format(username_field=self.username_field)
            raise serializers.ValidationError(msg)
