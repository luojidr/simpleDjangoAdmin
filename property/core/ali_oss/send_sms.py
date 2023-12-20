import json
import string
import random

from aliyunsdkcore.request import CommonRequest

from .base import AliOssBase


class AliSmsSend(AliOssBase):
    """ 阿里云发送sms服务 """
    ACCEPT_FORMAT = "json"
    PROTOCOL_TYPE = "https"     # https | http
    SMS_DOMAIN = "dysmsapi.aliyuncs.com"
    X_ACS_VERSION = "2017-05-25"

    def __init__(self,
                 phone_number,
                 template_param=None,
                 code_length=None,
                 country_code="86",
                 sign_name=None,
                 template_code=None,
                 **kwargs
                 ):
        super(AliSmsSend, self).__init__(**kwargs)

        self._code_length = code_length
        self._country_code = country_code
        self._phone_number = phone_number
        self._sign_name = sign_name or self.conf.INTERNAL_SIGN_NAME
        self._template_code = template_code or self.conf.INTERNAL_TEMPLATE_CODE
        self._template_param = template_param

        self._init_sms_sign_template()
        self._request = CommonRequest()

    def _add_body(self):
        self._request.set_accept_format(self.ACCEPT_FORMAT)
        self._request.set_domain(self.SMS_DOMAIN)
        self._request.set_method('POST')
        self._request.set_protocol_type(self.PROTOCOL_TYPE)
        self._request.set_version(self.X_ACS_VERSION)
        self._request.set_action_name('SendSms')

        self._request.add_query_param('RegionId', self._region_id)
        self._request.add_query_param('PhoneNumbers', self._phone_number)
        self._request.add_query_param('SignName', self._sign_name)
        self._request.add_query_param('TemplateCode', self._template_code)

        if self._template_param:
            self._request.add_query_param('TemplateParam', self._template_param)

    def _init_sms_sign_template(self):
        """ 如果短信签名来源变多，可做进一步拓展 """
        if self._country_code != "86":
            self._sign_name = self.conf.INTERNAL_SIGN_NAME
            self._template_code = self.conf.INTERNAL_TEMPLATE_CODE
            self._phone_number = self._country_code + self._phone_number
        else:
            self._sign_name = self.conf.SMS_SIGN_NAME_DIGITAL
            self._template_code = self.conf.SMS_TEMPLATE_CODE_DIGITAL

    def send_sms_code(self, sms_code=None):
        """ 发送单个sms """
        self._add_body()
        sms_entity = dict(code=sms_code) if sms_code else self.get_sms_code()
        self._request.add_query_param('TemplateParam', json.dumps(sms_entity))

        response = self._client.do_action_with_exception(self._request)
        result = str(response, encoding='utf-8')
        result_dict = json.loads(result)

        assert result_dict.get("Code") == "OK", "验证码发送错误:{}".format(result_dict.get("Message"))

        return dict(result_dict, smsCode=sms_entity["code"])

    def send_batch_sms(self):
        """ 批量发送sms """

    def get_sms_code(self, length=6):
        """ sms验证码 """
        length = self._code_length or length
        verify_code_list = [random.choice(string.digits) for _ in range(length)]
        sms_code = "".join(verify_code_list)

        return dict(code=sms_code)


