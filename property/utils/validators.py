import re
import inspect


class BaseValidator(object):
    def __init__(self, *args, **kwargs):
        if len(args) == 0:
            raise ValueError("验证器未传入验证对象")

        self.pattern_list = []
        self.target_object = args[0]

        for name, obj in inspect.getmembers(self):
            if not name.startswith("_") and name.endswith("REGEX"):
                self.pattern_list.append(obj)

    def validate(self):
        for pattern in self.pattern_list:
            m = pattern.match(self.target_object)
            if m is not None:
                return True

        return False

    def __call__(self, *args, **kwargs):
        return self.validate()


class PhoneValidator(BaseValidator):
    """ 手机号码验证器 """

    # 中国移动正则
    MOBILE_REGEX = re.compile(r"^1(?:34[0-8]|3[5-9]\d|5[0-2,7-9]\d|7[28]\d|8[2-4,7-8]\d|9[5,7,8]\d)\d{7}$")

    # 中国联通正则
    UNICOM_REGEX = re.compile(r"^1(?:3[0-2]|[578][56]|66|96)\d{8}$")

    # 中国电信正则
    TELECOM_REGEX = re.compile(r"^1(?:33|53|7[37]|8[019]|9[0139])\d{8}$")

    # 中国广电正则
    BROADCAST_REGEX = re.compile(r"^1(?:92)\d{8}$")

    # 中国移动(虚拟)正则
    VIRTUAL_MOBILE_REGEX = re.compile(r"^1(?:70[356]|65\d)\d{7}$")

    # 中国联通(虚拟)正则
    VIRTUAL_UNICOM_REGEX = re.compile(r"^1(?:70[4,7-9]|71\d|67\d)\d{7}$")

    # 中国电信(虚拟)正则
    VIRTUAL_TELECOM_REGEX = re.compile(r"^1(?:70[0-2]|62\d)\d{7}$")


class URLValidator(BaseValidator):
    """ 链接验证器 """
    URL_REGEX = re.compile(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+')


PhoneValidator("15958637603")()