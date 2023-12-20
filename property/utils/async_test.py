import time
from queue import Queue
import asyncio
import redis
from threading import Thread

loop = asyncio.new_event_loop()
queue = Queue()


def get_redis():
    connection_pool = redis.ConnectionPool(host='127.0.0.1', db=0)
    return redis.Redis(connection_pool=connection_pool)


# 创建redis连接
rcon = get_redis()


def start_loop(loop):
    print("start_loop:", loop, id(loop))
    # 一个在后台永远运行的事件循环
    # if not loop.closed():
    asyncio.set_event_loop(loop)
    loop.run_forever()


async def do_sleep(x, queue):
    await asyncio.sleep(x)
    queue.put("ok")
    print("do sleep over:", x)


def consumer():
    while True:
        task = rcon.rpop("queue")
        time.sleep(2)
        if not task:
            time.sleep(10)
            continue
        print(">>>>>>>>>>>>>>>>>")
        asyncio.run_coroutine_threadsafe(do_sleep(int(task), queue), loop)


def start_async():
    # 定义一个线程，运行一个事件循环对象，用于实时接收新任务
    loop_thread = Thread(target=start_loop, args=(loop,))
    # loop_thread.setDaemon(True)
    loop_thread.start()

    # 子线程：用于消费队列消息，并实时往事件对象容器中添加新任务
    consumer_thread = Thread(target=consumer)
    # consumer_thread.setDaemon(True)
    consumer_thread.start()
