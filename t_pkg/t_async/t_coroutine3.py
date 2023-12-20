import asyncio
# from asyncio import
from asyncio.futures import Future
from collections.abc import Coroutine, Awaitable


async def a():
    await asyncio.sleep(1)
    return 'A'


def callback(future):
    print(future, type(future))
    print(f'Result: {future.result()}')


async def main():
    loop = asyncio.get_event_loop()
    tmp_task = asyncio.create_task(a())
    print("tmp_task:", tmp_task, type(tmp_task))
    task = loop.create_task(a())
    print("task:", task, type(task))

    task.add_done_callback(callback)
    await task


if __name__ == "__main__":
    asyncio.run(main())




