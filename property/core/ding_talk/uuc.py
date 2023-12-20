import random
import os.path
import logging

import requests
from django.conf import settings
from django.db import transaction

from ...utils.decorators import to_retry
from ...utils.validators import PhoneValidator
from ...utils.exception import PhoneValidateError, UUCUserNotExistError
from fosun_circle.apps.users.models import (
    CircleUsersModel,
    CircleGroupModel,
    CircleGroupUsersModel,
    CircleUsersVirtualRoleModel
)

__all__ = ["UUCUser"]
logger = logging.getLogger("django")


class UUCUser(object):
    _uuc_url = settings.UUC_URL

    def __init__(self, phone, validator=PhoneValidator, **kwargs):
        self._phone = phone or ""
        self._validator = validator(phone)

        self._avatar = kwargs.get("avatar", "")

    @to_retry
    def get_uuc_user(self):
        """ 通过 UUC 接口获取用户信息
            返回值符合 UsersModel 字段
        """

        if not self._validator():
            raise PhoneValidateError()

        params = dict(mobile=self._phone)
        resp = requests.get(self._uuc_url, params=params, timeout=5)
        data = resp.json()

        if data.get("errcode") != 0:
            raise UUCUserNotExistError(self._phone)

        data = data.get("data", [{}])[0]
        detail_depart = data["department"][0] if data.get("department") else {}
        uuc_user = dict(
            username=data.get("fullname", ""), email=data.get("email", ""),
            state_code=data.get("stateCode", ""), phone_number=data.get("mobile", ""),
            position_chz=data.get("titleDesc", ""), position_eng=data.get("title_en", ""),
            department_chz=detail_depart.get("departmentName", ""),
            department_eng=detail_depart.get("departmentEnName", ""),
            ding_job_code=data.get("jobCode", ""), avatar=data.get("avatar", "") or self._avatar
        )

        return uuc_user

    def create_uuc_user(self):
        """ 通过 UUC, 创建或修改用户 """
        try:
            uuc_user = self.get_uuc_user()
        except UUCUserNotExistError:
            uuc_user = None
        except Exception as e:
            logger.warning("Mobile: %s, 调用uuc接口错误: %s", self._phone, str(e))
            return

        with transaction.atomic():
            if uuc_user is None:
                self._delete_circle_user()
            else:
                user_obj = self._add_or_update_circle_user(uuc_user=uuc_user)

        if uuc_user is None:
            logger.warning("通过uuc接口获取钉钉用户不存在, mobile: %s", self._phone)
            raise UUCUserNotExistError(self._phone)

        return user_obj

    @staticmethod
    def get_nick_name():
        """ 随机获取昵称 """
        file_path = os.path.join(settings.ROOT_DIR, settings.APP_NAME, "static")
        filename = os.path.join(file_path, "nick_name.txt")

        with open(filename, "r", encoding="utf-8") as fp:
            nick_name_list = fp.readlines() or [""]
            return random.choice(nick_name_list).strip()

    @staticmethod
    def get_avatar_url():
        """ 随机获取默认头像 """
        avatar_url = settings.DEFAULT_AVATAR_URL % random.randint(1, 101)
        return avatar_url

    def _delete_circle_user(self):
        """ 删除用户及相关 """
        group_obj, is_ok_group = CircleGroupModel.objects.get_or_create(name="复星集团")
        user_obj = CircleUsersModel.objects.filter(phone_number=self._phone, is_del=False).first()

        if user_obj is not None:
            user_obj.employee_status = 2
            user_obj.is_del = True
            user_obj.save()

            master_virtual_obj = CircleUsersVirtualRoleModel.objects \
                .filter(user_id=user_obj.id, role_type=0, is_del=False) \
                .first()

            if master_virtual_obj is not None:
                master_virtual_obj.is_del = True
                master_virtual_obj.save()

            group_user_obj = CircleGroupUsersModel.objects \
                .filter(group_id=group_obj.id, user_id=user_obj.id, is_del=False) \
                .first()

            if group_user_obj is not None:
                group_user_obj.is_del = True
                group_user_obj.save()

    def _add_or_update_circle_user(self, uuc_user):
        """ 新增用户及相关
        :param uuc_user, dict
        """
        group_obj, is_ok_group = CircleGroupModel.objects.get_or_create(name="复星集团")
        user_obj = CircleUsersModel.objects.filter(phone_number=self._phone, is_del=False).first()

        if user_obj is None:
            user_obj = CircleUsersModel(source="UUC", **uuc_user)
            user_obj.set_password(CircleUsersModel.DEFAULT_PASSWORD)
            user_obj.save()
        else:
            # 更新用户基本信息
            for key, value in uuc_user.items():
                attr_val = user_obj.__dict__.get(key)

                if value and attr_val != value:
                    user_obj.__dict__[key] = value

            user_obj.save()

        master_virtual_obj = CircleUsersVirtualRoleModel.objects \
            .filter(user_id=user_obj.id, role_type=0, is_del=False) \
            .first()

        if master_virtual_obj is None:
            nick_name = self.get_nick_name()
            CircleUsersVirtualRoleModel.objects.create(
                user_id=user_obj.id,
                role_avatar=user_obj.avatar,
                nick_name=nick_name
            )

        group_user_obj = CircleGroupUsersModel.objects \
            .filter(group_id=group_obj.id, user_id=user_obj.id, is_del=False) \
            .first()

        if group_user_obj is None:
            CircleGroupUsersModel.objects.create(group_id=group_obj.id, user_id=user_obj.id)

        return user_obj

