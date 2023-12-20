import time
import collections
import types
import typing
import asyncio
from contextlib import asynccontextmanager


async def a():
    print('Suspending a')
    await asyncio.sleep(3)
    print('Resuming a')
    return 'A'


async def b():
    print('Suspending b')
    await asyncio.sleep(1)
    print('Resuming b')
    return 'B'


def create_task(coro):
    loop = asyncio.events.get_running_loop()
    # asyncio.create_task(coro)
    return loop.create_task(coro)


async def s1():
    return await asyncio.gather(a(), b())


@asynccontextmanager
async def async_timed(func):
    start = time.perf_counter()
    yield await func()
    print(f'Cost: {time.perf_counter() - start}')


async def main():
    async with async_timed(s1) as rv:
        print(f'Result: {rv}')


async def async_run():
    # ************************* OK **************************
    ra, rb = await asyncio.gather(a(), b())
    # print(ra, rb)
    # ************************* OK **************************

    # ************************* OK **************************
    # DeprecationWarning: The explicit passing of coroutine objects to asyncio.wait() is deprecated since Python 3.8,
    # and scheduled for removal in Python 3.11.
    done, pending = await asyncio.wait([a(), b()], return_when=asyncio.FIRST_COMPLETED)
    print(done)
    print(pending)
    print(list(done)[0])
    # ************************* OK **************************


if __name__ == "__main__":
    # asyncio.run(async_run())

    asyncio.run(main())

    # ************** Test ******************
    # task_a = asyncio.shield(a())
    # ************** Test ******************



