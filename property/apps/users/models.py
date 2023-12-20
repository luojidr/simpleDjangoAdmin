from datetime import datetime

from django.db import models
from django.db.models import Q
from django.db.models import ObjectDoesNotExist
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError

from core.db.base import BaseModelMixin


class UsersModel(AbstractUser, BaseModelMixin):
    """ 用户基本信息 """
    GENDER_CHOICES = [
        ('M', '男'),
        ('F', '女'),
        ('U', '保密')
    ]

    is_superuser = models.BooleanField(default=False, verbose_name="是否超级管理员")
    avatar = models.CharField(verbose_name="头像链接", max_length=500, default='')
    name_chz = models.CharField(max_length=200, verbose_name='中文名', default='')
    name_eng = models.CharField(max_length=200, verbose_name='英文名', default='')
    gender = models.SmallIntegerField(choices=GENDER_CHOICES, default=3, verbose_name='性别')
    birthday = models.DateField(verbose_name="出生日期", default="1979-01-01")
    mobile = models.CharField(max_length=20, default="", unique=True, verbose_name="手机号码")
    state_code = models.CharField(max_length=10, default='+86', verbose_name='手机国家码')
    company = models.CharField(max_length=200, verbose_name='公司名', default='')
    department = models.CharField(max_length=500, verbose_name='部门', default='')
    position = models.CharField(max_length=500, verbose_name='职位', default="")
    source = models.CharField(max_length=20, verbose_name="用户来源", default="SYS")

    class Meta:
        db_table = "users"
        ordering = ['-id']
        verbose_name = "用户"
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.get_username()


class CaptchaTemplateModel(BaseModelMixin):
    """ 验证码模板 """
    CAPTCHA_TYPE_CHOICE = [
        (1, "邮箱注册验证码"),
        (2, "短信注册验证码"),
    ]

    template_type = models.IntegerField("验证码类型", unique=True, choices=CAPTCHA_TYPE_CHOICE, default=1)
    html_template = models.CharField("验证码模板", max_length=1000, default="")

    class Meta:
        db_table = "user_captcha_template"
        verbose_name = "验证码模板"
        verbose_name_plural = verbose_name


class UserCaptchaCodeModel(BaseModelMixin):
    """ 用户验证码详情 """
    CAPTCHA_TYPE_CHOICE = [
        (1, "邮箱校验"),
        (2, "手机校验"),
    ]

    mobile = models.CharField("手机号", max_length=11, db_index=True, default="")
    email = models.CharField("邮箱", max_length=100, db_index=True, default="")
    captcha = models.CharField("验证码", max_length=10, db_index=True, default="")
    captcha_type = models.IntegerField("校验类型", choices=CAPTCHA_TYPE_CHOICE, default=1)
    template = models.ForeignKey(to=CaptchaTemplateModel, related_name="captcha_template",
                                 on_delete=models.CASCADE, help_text="验证码类型")

    class Meta:
        db_table = "user_captcha_code"
        verbose_name = "用户验证码详情 "
        verbose_name_plural = verbose_name

    @classmethod
    def validate_expiration(cls, captcha, email=None,  **kwargs):
        """ 校验验证码过期时间 """
        criterion = [Q(captcha=captcha)]
        email and criterion.append(Q(email=email))
        kwargs.get("mobile") and criterion.append(Q(mobile=kwargs["mobile"]))

        captcha_queryset = cls.objects.filter(*criterion).order_by("-create_time")
        if not captcha_queryset:
            raise ObjectDoesNotExist("验证码不存在")

        expire_seconds = kwargs.get("kwargs", 20) * 60
        elapse_seconds = (datetime.now() - captcha_queryset[0].create_time).total_seconds()

        if elapse_seconds > expire_seconds:
            raise ValidationError("验证码已失效")

        return True

