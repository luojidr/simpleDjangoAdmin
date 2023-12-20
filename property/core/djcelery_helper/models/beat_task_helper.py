import pytz
from django.db import models
from django.conf import settings
from celery.schedules import crontab
from django_celery_beat.models import CrontabSchedule


def get_crontabschedule(params=None):
    get_t = (lambda k: (params.get(k) or "").strip())
    cron_obj, is_create = CrontabSchedule.objects.get_or_create(
        minute=get_t("minute"), hour=get_t("hour"),
        day_of_month=get_t("day_of_month"), month_of_year=get_t("month_of_year"),
        day_of_week=get_t("day_of_week"), timezone=pytz.timezone(settings.TIME_ZONE)
    )

    return cron_obj, is_create


class BeatExtraTaskHelperModel(models.Model):
    name = models.CharField("Task Name", max_length=500, default='')
    # task_path = models.CharField("Task Path", max_length=1000, default='')
    broker_url = models.CharField("Broker Url", max_length=500, default='')
    queue_name = models.CharField("Queue Name", max_length=200, default='')
    exchange_name = models.CharField("Exchange Name", max_length=200, default='')
    routing_key = models.CharField("Route Key", max_length=200, default='')
    crontab_id = models.IntegerField("Crontab", default=0)
    enable = models.SmallIntegerField("Enable or not", default=1)
    func_name = models.CharField("Func Name", max_length=100, default='')
    task_source_code = models.CharField("Task Source Code", max_length=5000, default='')
    task_name = models.CharField("Task Name", max_length=200, default='')
    remark = models.CharField("remark", max_length=1000, default='')

    class Meta:
        ordering = ['-id']
        db_table = 'djcelery_helper_beat_extra_tasks'
        app_label = 'common'

    @classmethod
    def get_enable_tasks(cls):
        return cls.objects.filter(enable=True).all()

    @classmethod
    def create_object(cls,  **kwargs):
        """ 创建对象 """
        fields = [f.name for f in cls._meta.concrete_fields]
        new_kwargs = {key: value for key, value in kwargs.items() if key in fields}

        cron_obj, is_create = get_crontabschedule(new_kwargs)
        new_kwargs["crontab_id"] = cron_obj.id
        extra_task = cls.objects.create(**new_kwargs)

        return extra_task

    def exec_task_func(self):
        if not self.task_source_code:
            return

        namespace = {}
        exec(self.task_source_code.strip(), namespace)
        func = namespace.get(self.func_name)

        assert func, "Task Helper object<%s> not exist func<%s>" % (self.id, self.func_name)
        return func

    def get_crontab(self):
        cron_obj = CrontabSchedule.objects.get(id=self.crontab_id)
        return crontab(
            minute=cron_obj.minute, hour=cron_obj.hour, day_of_week=cron_obj.day_of_week,
            day_of_month=cron_obj.day_of_month, month_of_year=cron_obj.month_of_year
        )

