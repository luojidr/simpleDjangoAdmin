from enum import unique

from .base import EnumBase


class BaseEnum(EnumBase):
    @property
    def code(self):
        return self.value[0]

    @property
    def msg(self):
        return self.value[1]


@unique
class StatusEnum(BaseEnum):
    OK = (200, "ok")
    FAILED = (1000, 'failed')
    LOGIN_FAIL = (1001, "用户名或密码错误")


