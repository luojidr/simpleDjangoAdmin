import os.path
import json
import time
import traceback

import requests
from django.conf import settings

from config import celery_app
from property.utils.log import task_logger as logger


@celery_app.task
def sync_users_from_spider(*args, **kwargs):
    """ 通过百家姓爬取复星集团所有员工 """
    # chz_list = ["赵", "钱", "孙", "李"]
    chz_list = list(args)
    logger.info("XXX args: %s, kwargs: %s", chz_list, kwargs)

    api = "https://sun.com/fosun/v1.0/fosun_scampaign/search_personnel_info"
    headers = {"Content-Type": "application/json;charset=UTF-8"}

    logger.info("爬取集团用户信息 UUCURL: %s" % settings.UUC_URL)
    max_limit = 5 if settings.DEBUG else 100000

    for index, chz in enumerate(chz_list[:max_limit]):
        form_data = dict(mobile="13601841820", p_name=chz, limit=10000)
        res = requests.post(api, data=json.dumps(form_data), headers=headers)

        if res.status_code == 200:
            for user_item in res.json()["result"]["result"]:
                name = user_item["name"]
                mobile = user_item["mobile"]
                avatar = user_item["avatar"]

                try:
                    logger.info("爬取 Index：%s, Name: %s, mobile: %s 成功！" % (index, name, mobile))
                except Exception:
                    logger.info("爬取 Index：%s, Name: %s, mobile: %s 失败！" % (index, name, mobile))
                    logger.error(traceback.format_exc())
        else:
            logger.info("接口错误 Index：{}, form_data: {}".format(index, form_data))
