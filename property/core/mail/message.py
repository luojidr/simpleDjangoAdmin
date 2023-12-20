import random
import string

from django.conf import settings
from django.core.mail import send_mail

from .template import MailTemplate, MailHtmlTemplateEnum


class EmailSender(object):
    """ 邮件发送器 """
    def __init__(self, template_type=None, html_template=None):
        if template_type:
            self.mail_template = MailTemplate(template_type, html_template)
        else:
            self.mail_template = None

        self.template_type = template_type

    def random_code(self, size=4):
        cha_list = random.choices(string.ascii_letters + string.digits, k=size)
        return "".join(cha_list)

    def send_mail(self, recipient_list,
                  subject=None, from_email=None, message="",
                  fail_silently=False, html_message=None):
        render_kwargs = {}

        if from_email:
            from_email = settings.EMAIL_FROM

        if self.mail_template:
            subject = subject or self.mail_template.template_info["subject"]

        if self.template_type == MailHtmlTemplateEnum.USER_REGISTER.type:
            render_kwargs["email_code"] = self.random_code()

        html_message = html_message or self.mail_template.render_mail_template(**render_kwargs)

        num_sent = send_mail(
            subject=subject, message=message, from_email=from_email,
            recipient_list=recipient_list, fail_silently=fail_silently,
            html_message=html_message
        )

        render_kwargs["num_sent"] = num_sent
        return render_kwargs

    def send_mass_mail(self):
        pass







