import asyncio
import time


async def _sleep(x):
    # time.sleep(x)
    await asyncio.sleep(x)
    return '暂停了{}秒！'.format(x)


async def main():
    await asyncio.gather(*[_sleep(i) for i in range(5)])


# coroutine = _sleep(2)
# loop = asyncio.get_event_loop()
#
# task = asyncio.ensure_future(coroutine)
# loop.run_until_complete(task)
# loop.close()
# task.result() 可以取得返回结果
# print('返回结果：{}'.format(task.result()))


# ***********************************
start = time.time()
asyncio.run(main())
print("Total Spend: %ss" % (time.time() - start))


