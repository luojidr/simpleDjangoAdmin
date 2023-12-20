import enum
from collections import namedtuple

from django.conf import settings

__all__ = ["MailTemplate", "MailHtmlTemplateEnum"]


class MailEnumBase(enum.Enum):
    @property
    def type(self):
        return self.value[0]

    @property
    def name(self):
        return self.value[1]

    @property
    def subject(self):
        return self.value[2]


class MailHtmlTemplateEnum(MailEnumBase):
    """ 模板唯一性 """
    USER_REGISTER = (100, "用户注册邮件验证码", "【AweSome】邮箱验证码通知")


class MailTemplate(object):
    mail_html_template_cls = MailHtmlTemplateEnum

    def __init__(self, template_type=None, html_template=None):
        self.template_type = template_type
        self.html_template = html_template

        self._template_info = None
        self._template_name_label = "{key}_MAIL_HTML_TEMPLATE_{type}"

        self._validate()

    def _validate(self):
        template_enums = self.mail_html_template_cls.__members__
        template_mapping = {
            enum_obj.type: dict(name=enum_obj.name, key=enum_key)
            for enum_key, enum_obj in template_enums.items()
        }

        if self.template_type not in template_mapping:
            raise ValueError("不存在该邮件模板类型, TemplateType: %s" % self.template_type)

        if not self.html_template:
            mail_template = template_mapping[self.template_type]
            key = mail_template["key"]
            mail_template_name = self._template_name_label.format(key=key, type=self.template_type)

            if not getattr(settings, mail_template_name, False):
                name = template_mapping[self.template_type]["name"]
                raise ValueError("未发现【%s】的模板" % name)

    @property
    def template_info(self):
        if self._template_info:
            return self._template_info

        template_enums = self.mail_html_template_cls.__members__
        template_mapping = {
            enum_obj.type: dict(name=enum_obj.name, key=enum_key, subject=enum_obj.subject)
            for enum_key, enum_obj in template_enums.items()
        }

        mail_template_data = template_mapping[self.template_type]
        template_var = self._template_name_label.format(key=mail_template_data["key"], type=self.template_type)
        self.html_template = getattr(settings, template_var)

        self._template_info = dict(
            type=self.template_type,
            html_template=self.html_template,
            **mail_template_data
        )
        return self._template_info

    def render_mail_template(self, **render_kwargs):
        """ 邮件模板 """
        template_info = self.template_info
        html_template = template_info["html_template"]

        return html_template.format(**render_kwargs)


