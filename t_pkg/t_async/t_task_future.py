import asyncio
from asyncio import Task, Future


async def my_coroutine():
    await asyncio.sleep(1)

# RuntimeError: no running event loop
# 该函数在 Python 3.7 中被加入，更加高层次的函数，返回Task对象
# loop = asyncio.get_event_loop()
# # future1 = asyncio.create_task(my_coroutine())
# future1 = loop.create_task(my_coroutine())
# loop.run_until_complete(future1)

# RuntimeError: no running event loop
# 在Python 3.7 之前，是更加低级的函数，返回Future对象或者Task对象
# future2 = asyncio.ensure_future(my_coroutine())



import asyncio
import time


async def compute(x, y):
    print("Compute {} + {}...".format(x, y))
    await asyncio.sleep(2.0)
    return x+y


async def print_sum(x, y):
    result = await compute(x, y)
    print("{} + {} = {}".format(x, y, result))


start = time.time()
loop = asyncio.get_event_loop()
tasks = [
    asyncio.create_task(print_sum(0, 0)),  # RuntimeError: no running event loop
    asyncio.ensure_future(print_sum(1, 1)),
    asyncio.ensure_future(print_sum(2, 2)),
]
loop.run_until_complete(asyncio.wait(tasks))
loop.close()
print("Total elapsed time {}".format(time.time() - start))
