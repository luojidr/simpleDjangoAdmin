import time
import asyncio
import os, sys, django

from multiprocessing.dummy import Pool as ThreadPool

# sys.path.append(r"D:/workplace/py_workship/fosun_circle")

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.prod")
django.setup()

from property.apps.users.tasks.task_spider_users import sync_users_from_spider
from property.apps.users.tasks.task_concurrency_limit import test_concurrency_limit


def send_spider():
    # spider_args = ["赵", "钱", "孙", "李", "周",	"吴", "郑", "王", "冯", "陈", "褚", "卫",	"蒋", "沈",	"韩", "杨"]
    spider_args = ["诸葛"]

    for index, name in enumerate(spider_args):
        if index % 3 == 0:
            sync_users_from_spider.apply_async(args=(name,), kwargs=dict(index=index), priority=9)
        else:
            sync_users_from_spider.apply_async(args=(name,), kwargs=dict(index=index))


def send_concurrency_limit():
    start = time.time()
    for _ in range(10000):
        test_concurrency_limit.delay()

    # Sync Spend: 11.882311582565308
    print("Sync Spend:", time.time() - start)


def send_one_by_one(*args, **kwargs):
    test_concurrency_limit.delay()


async def send_msg_to_mq():
    test_concurrency_limit.delay()


async def async_send():
    await send_msg_to_mq()


async def async_run():
    # Async Spend: 11.619438409805298
    coros = [async_send() for _ in range(10000)]
    await asyncio.gather(*coros)


def run():
    start_t = time.monotonic()
    loop = asyncio.get_event_loop()
    tasks = [asyncio.ensure_future(async_send()) for _ in range(10000)]
    loop.run_until_complete(asyncio.wait(tasks))

    # run_by_threading_pool -> Async run Spend: 15.87514341098722
    print("Async run Spend:", time.monotonic() - start_t)


def run_by_threading_pool():
    start_t = time.monotonic()

    pool = ThreadPool()
    pool.map_async(send_one_by_one, [i for i in range(10000)])
    pool.close()
    pool.join()

    # run_by_threading_pool -> Async run Spend: 15.87514341098722
    print("run_by_threading_pool -> Async run Spend:", time.monotonic() - start_t)


if __name__ == "__main__":
    # send_concurrency_limit()      # 同步1

    # async 与 同步1 花费时间接近，似乎未达到异步效果
    # start_t = time.monotonic()
    # asyncio.run(async_run())
    # print("Async Spend:", time.monotonic() - start_t)

    # Async 与 同步1 花费时间接近，似乎未达到异步效果
    # run()

    # run_by_threading_pool()

    # print(bin(3232235521))


    # Test
    t = test_concurrency_limit.delay()

    while 1:
        time.sleep(1)
        print(t.state)



