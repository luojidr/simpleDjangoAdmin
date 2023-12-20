from ..constant.enums.status_code import CodeMessageEnum


class BaseError(Exception):
    def __init__(self, msg, code=CodeMessageEnum.INTERNAL_ERROR.code):
        self.msg = msg
        self.code = code

    def to_dict(self):
        return dict(code=self.code, message=self.msg)


class SerializerNotExist(BaseError):
    def __init__(self):
        self.msg = CodeMessageEnum.SERIALIZER_NOT_EXIST.message
        self.code = CodeMessageEnum.SERIALIZER_NOT_EXIST.code
        BaseError.__init__(self, self.msg, self.code)


class DingMsgTypeNotExist(BaseError):
    def __init__(self, msg_type):
        self.code = CodeMessageEnum.DING_MSG_TYPE_NOT_EXIST.code
        self.msg = CodeMessageEnum.DING_MSG_TYPE_NOT_EXIST.message.format(msg_type=msg_type)
        BaseError.__init__(self, self.msg, self.code)


class PhoneValidateError(BaseError):
    def __init__(self):
        self.code = CodeMessageEnum.PHONE_VALIDATE_ERROR.code
        self.msg = CodeMessageEnum.PHONE_VALIDATE_ERROR.message
        BaseError.__init__(self, self.msg, self.code)


class UUCUserNotExistError(BaseError):
    def __init__(self, mobile):
        self.code = CodeMessageEnum.UUC_USER_NOT_EXIST_ERROR.code
        self.msg = CodeMessageEnum.UUC_USER_NOT_EXIST_ERROR.message
        BaseError.__init__(self, self.msg % mobile, self.code)


class SmsCodeError(BaseError):
    def __init__(self):
        self.code = CodeMessageEnum.SMS_CODE_ERROR.code
        self.msg = CodeMessageEnum.SMS_CODE_ERROR.message
        BaseError.__init__(self, self.msg, self.code)


class ValidationError(BaseError):
    def __init__(self, msg):
        self.code = CodeMessageEnum.VALIDATION_ERROR.code
        self.msg = CodeMessageEnum.VALIDATION_ERROR.message % msg
        BaseError.__init__(self, self.msg, self.code)


class ObjectTypeNotMatchError(BaseError):
    def __init__(self, msg):
        self.code = CodeMessageEnum.OBJECT_TYPE_NOT_MATCH.code
        self.msg = CodeMessageEnum.OBJECT_TYPE_NOT_MATCH.message % msg
        BaseError.__init__(self, self.msg, self.code)


class AuthenticationFailed(BaseError):
    def __init__(self, msg):
        self.code = 401
        self.msg = "请求认证失败, 详情：%s" % msg
        BaseError.__init__(self, self.msg, self.code)


class CreateBucketAccountKeyError(BaseError):
    def __init__(self):
        self.code = CodeMessageEnum.CREATE_BUCKET_ACCOUNT.code
        self.msg = CodeMessageEnum.CREATE_BUCKET_ACCOUNT.message
        BaseError.__init__(self, self.msg, self.code)


