import numbers
from collections.abc import Mapping
from datetime import timedelta, datetime

from celery.app.amqp import AMQP, task_message
from celery.utils.nodenames import anon_nodename
from celery.utils.saferepr import saferepr
from celery.utils.time import maybe_make_aware

__all__ = ["Amqp"]


class Amqp(AMQP):
    lang = 'py'

    def as_task_v2(self, task_id, name, args=None, kwargs=None,
                   countdown=None, eta=None, group_id=None, group_index=None,
                   expires=None, retries=0, chord=None,
                   callbacks=None, errbacks=None, reply_to=None,
                   time_limit=None, soft_time_limit=None,
                   create_sent_event=False, root_id=None, parent_id=None,
                   shadow=None, chain=None, now=None, timezone=None,
                   origin=None, ignore_result=False, argsrepr=None, kwargsrepr=None):
        args = args or ()
        kwargs = kwargs or {}
        lang = kwargs.pop("lang", None) or self.lang

        if not isinstance(args, (list, tuple)):
            raise TypeError('task args must be a list or tuple')
        if not isinstance(kwargs, Mapping):
            raise TypeError('task keyword arguments must be a mapping')

        if countdown:  # convert countdown to ETA
            self._verify_seconds(countdown, 'countdown')
            now = now or self.app.now()
            timezone = timezone or self.app.timezone
            eta = maybe_make_aware(now + timedelta(seconds=countdown), tz=timezone)

        # expires 整型，浮点型均为实数 (numbers.Real)
        if isinstance(expires, numbers.Real):
            self._verify_seconds(expires, 'expires')
            now = now or self.app.now()
            timezone = timezone or self.app.timezone
            expires = maybe_make_aware(now + timedelta(seconds=expires), tz=timezone)

        if not isinstance(eta, str):
            eta = eta and eta.isoformat()

        # If we retry a task `expires` will already be ISO8601-formatted.
        if not isinstance(expires, str):
            expires = expires and expires.isoformat()

        if argsrepr is None:
            argsrepr = saferepr(args, self.argsrepr_maxsize)
        if kwargsrepr is None:
            kwargsrepr = saferepr(kwargs, self.kwargsrepr_maxsize)

        if not root_id:  # empty root_id defaults to task_id
            root_id = task_id

        headers = dict(
            lang=lang, task=name, id=task_id, shadow=shadow,
            eta=eta, expires=expires, group=group_id, group_index=group_index,
            retries=retries, timelimit=[time_limit, soft_time_limit], root_id=root_id,
            parent_id=parent_id, argsrepr=argsrepr, kwargsrepr=kwargsrepr,
            origin=origin or anon_nodename(), ignore_result=ignore_result,
        )
        properties = dict(correlation_id=task_id, reply_to=reply_to or "")
        sent_event = dict(
            uuid=task_id, root_id=root_id, parent_id=parent_id, name=name,
            args=argsrepr, kwargs=kwargsrepr, retries=retries, eta=eta, expires=expires
        ) if create_sent_event else None
        payload = self.get_payload(args, kwargs, lang=lang)

        return task_message(headers=headers, properties=properties, body=payload, sent_event=sent_event)

    def get_payload(self, args, kwargs, lang=None):
        lang = lang or self.lang

        if lang == 'py':
            # celery规范：(args, kwargs, {}); 如果适应其他开发语言(eg:java), 改造后celery发送消息 OK, 但不能消费
            payload = (args, kwargs, {})  # default python
        elif lang == 'java':
            payload = kwargs
        elif lang == 'go':
            pass

        return payload
