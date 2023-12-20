import sys
import json
import logging
import traceback

from celery.exceptions import reraise
from celery.beat import SchedulingError
from celery.beat import _evaluate_entry_args, _evaluate_entry_kwargs

from django.db import transaction
from django_celery_beat.schedulers import DatabaseScheduler as DJCeleryBeatScheduler

from ..models.beat_task_helper import BeatExtraTaskHelperModel

TaskHelperModel = BeatExtraTaskHelperModel
logger = logging.getLogger("celery.beat")  # Recommended use celery.beat with django


class DatabaseScheduler(DJCeleryBeatScheduler):
    EXTRA_TASK_CACHE = {}  # 如果多服务，会重复执行

    def apply_async(self, entry, producer=None, advance=True, **kwargs):
        """ Override: Send different messages based on the `broker_url`
        eg:
            >>> result = super().apply_async()
        """
        # Update time-stamps and run counts before we actually execute,
        # so we have that done if an exception is raised (doesn't schedule
        # forever.)
        entry = self.reserve(entry) if advance else entry
        task = self.app.tasks.get(entry.task)

        logger.info("[%s] >>> task: %s, default broker: %s", __name__, task and task.name, self.app.conf.broker_url)

        try:
            entry_args = _evaluate_entry_args(entry.args)
            entry_kwargs = _evaluate_entry_kwargs(entry.kwargs)

            # Maybe broker_url is different, then send native message
            if task and task.name in self.EXTRA_TASK_CACHE:
                task_name = task.name
                extra_task_id = self.EXTRA_TASK_CACHE[task_name]['id']

                extra_task_obj = TaskHelperModel.get_enable_tasks().filter(id=extra_task_id).first()
                broker_url = extra_task_obj and extra_task_obj.broker_url or None

                if self.app.conf.broker_url != broker_url:
                    logger.info("[%s] >>> beat to periodic task, name: %s", __name__, task_name)
                    queue_name = (extra_task_obj.queue_name or "").strip()
                    exchange_name = (extra_task_obj.exchange_name or "").strip()
                    routing_key = (extra_task_obj.routing_key or "").strip()

                    return task.apply_async(entry_args, entry_kwargs, producer=None,
                                            is_native=True, broker_url=broker_url, queue_name=queue_name,
                                            exchange_name=exchange_name, routing_key=routing_key,
                                            **entry.options)

            # native app to send message
            if task:
                return task.apply_async(entry_args, entry_kwargs,
                                        producer=producer,
                                        **entry.options)
            else:
                return self.send_task(entry.task, entry_args, entry_kwargs,
                                      producer=producer,
                                      **entry.options)
        except Exception as exc:  # pylint: disable=broad-except
            val = SchedulingError("Couldn't apply scheduled task {0.name}: {exc}".format(entry, exc=exc))
            reraise(SchedulingError, val, sys.exc_info()[2])
        finally:
            self._tasks_since_sync += 1
            if self.should_sync():
                self._do_sync()

    def schedule_changed(self):
        is_changed = super().schedule_changed()

        try:
            cached_ids = [item['id'] for item in self.EXTRA_TASK_CACHE.values()]
            enable_queryset = TaskHelperModel.get_enable_tasks().exclude(id__in=cached_ids).all()

            for task_obj in enable_queryset:
                self._add_to_scheduler(extra_task_obj=task_obj)
        except Exception as e:
            logger.error("[%s] >>> schedule_changed err: %s", __name__, e)
            logger.error(traceback.format_exc())

        return is_changed

    def _add_to_scheduler(self, extra_task_obj):
        task_id = extra_task_obj.id

        if extra_task_obj.task_name not in self.EXTRA_TASK_CACHE:
            func = extra_task_obj.exec_task_func()
            if not func:
                return

            task = self.app.task(func)
            self.app.tasks.register(task)  # Register task to celery_app.apps.tasks

            task_name = task.name
            # entry: celery_app.conf.beat_schedule
            entry_fields = dict(
                task=task_name, options={'expire_seconds': None},
                schedule=extra_task_obj.get_crontab(),
                args=(), kwargs={},
            )

            if extra_task_obj.task_name != task_name:
                extra_task_obj.task_name = task_name
                extra_task_obj.save()

            self.Entry.from_entry(extra_task_obj.func_name, app=self.app, **entry_fields)
            self.EXTRA_TASK_CACHE[task_name] = dict(id=task_id, func=func)

