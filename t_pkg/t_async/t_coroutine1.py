import asyncio
import time
import types
import logging
import asyncio


async def coro_a():
    print("Suspending coro_a")
    await asyncio.sleep(3)
    print("running coro_a")
    return 100


async def coro_b():
    print("Suspending coro_b")
    await asyncio.sleep(1)
    print("running coro_b")
    return [1, 23, 45]


async def c():
    print('Inner C')
    return dict(c="abc")


async def sync_run():
    """ 其实是同步执行 """
    await coro_a()
    await coro_b()


async def async_run():
    # ************************* OK **************************
    # await asyncio.gather(coro_a(), coro_b())      # 异步
    # await asyncio.wait([coro_a(), coro_b()])      # 异步 Py3.11 will removal asyncio.wait
    # ************************* OK **************************

    # ************************* OK **************************
    # task_a = asyncio.create_task(coro_a())
    # task_b = asyncio.create_task(coro_b())
    # await task_a
    # await task_b
    # ************************* OK **************************

    # ************************* OK **************************
    ret_b = asyncio.create_task(coro_b())

    await coro_a()
    a = 100
    b = 200
    logging.error("t_test: %s, ret_b:%s", a + b, ret_b)
    # await c()
    await ret_b
    # ************************* OK **************************

    # ************************* Fail **************************
    # 同步 -> 直接await task不会对并发有帮助
    # await asyncio.create_task(coro_a())
    # await asyncio.create_task(coro_b())
    # ************************* Fail **************************

    # ************************* OK **************************
    # task = asyncio.ensure_future(coro_a())
    # await coro_b()
    # await task
    # ************************* OK **************************

    # ************************* OK **************************
    # loop = asyncio.get_event_loop()
    # task = loop.create_task(coro_a())
    # await coro_b()
    # await task
    # ************************* OK **************************


def show_perf(func):
    print("*" * 20)
    start = time.perf_counter()
    asyncio.run(func())
    print(f'{func.__name__} Cost: {time.perf_counter() - start}')


if __name__ == "__main__":
    # show_perf(sync_run)  # 同步

    show_perf(async_run)  # 异步

    # asyncio.run(async_run())





