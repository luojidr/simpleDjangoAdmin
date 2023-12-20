from __future__ import absolute_import

from celery import Celery as BaseCelery
from kombu.utils.objects import cached_property

import deprecated
from deprecated import deprecated

__all__ = ["Celery"]


@deprecated(reason="Custom Celery class is deprecated, use celery.Celery please!")
class Celery(BaseCelery):
    beat_cls = 'celery.apps.beat:Beat'

    def __init__(self, beat_cls=None, **kwargs):
        super().__init__(**kwargs)

        self.beat_cls = beat_cls or self.beat_cls

    @cached_property
    def Beat(self, **kwargs):
        """:program:`celery beat` scheduler application.

        See Also:
            :class:`~@Beat`.
        """
        return self.subclass_with_self(self.beat_cls)

