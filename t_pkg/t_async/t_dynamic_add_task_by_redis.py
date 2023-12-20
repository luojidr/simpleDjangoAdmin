""" 简单的动态异步任务 """


import time
import redis
import asyncio
from queue import Queue
import threading


def start_loop(loop):
    # 一个在后台永远运行的事件循环
    asyncio.set_event_loop(loop)
    loop.run_forever()      # 阻塞的


async def do_sleep(x, queue):
    await asyncio.sleep(x)
    queue.put("ok")


def get_redis():
    connection_pool = redis.ConnectionPool(host="127.0.0.1", db=0)
    return redis.Redis(connection_pool=connection_pool)


def consumer():
    while 1:
        task = rcon.rpop("queue")

        if not task:
            time.sleep(1)
            continue

        asyncio.run_coroutine_threadsafe(do_sleep(int(task), queue), loop=new_loop)


if __name__ == '__main__':
    print("1:", time.ctime())
    new_loop = asyncio.get_event_loop()

    # 守护线程： t..setDaemon(True)。主线程A中，创建了子线程B，并且在主线程A中调用了B.setDaemon(),这个的意思是，
    #           把主线程A设置为守护线程，这时候，要是主线程A执行结束了，就不管子线程B是否完成,一并和主线程A退出.
    #           这就是setDaemon方法的含义，这基本和join是相反的。此外，还有个要特别注意的：必须在start() 方法调用之前设置，
    #           如果不设置为守护线程，程序会被无限挂起。
    #
    # 守护线程的3中情况：
    # (1): 正常主线程结束了， 那么线程执行结束后也会退出(若子线程有死循环， 则子线程一致运行)
    # (2): 如果主线程是永远都不会结束的，那设置一个线程为守护线程是没必要的，设不设置都一样。
    # (3): 如果希望子线程一直运行， 可以把子线程的代码写在while True里面一直循环，但同时要设置为守护线程，
    #      不然主线程结束了，子线程还一直运行，程序结束不了； 设置了守护线程，则主程序结束，子线程也会结束(即使子线程中有死循环)
    #
    # join() 方法：主线程A中，创建了子线程B，并且在主线程A中调用了B.join()，那么，主线程A会在调用的地方等待，
    #              直到子线程B完成操作后，才可以接着往下执行，那么在调用这个线程时可以使用被调用线程的join方法。

    # 定义一个线程，运行一个事件循环对象，用于实时接收新任务
    loop_thread = threading.Thread(target=start_loop, args=(new_loop,))
    loop_thread.setDaemon(True)
    loop_thread.start()

    # 创建redis连接
    rcon = get_redis()

    rcon.lpush("queue", 1, 2, 3, 4,5 , 6)

    queue = Queue()

    # 子线程：用于消费队列消息，并实时往事件对象容器中添加新任务
    consumer_thread = threading.Thread(target=consumer)
    consumer_thread.setDaemon(True)
    consumer_thread.start()

    while True:
        msg = queue.get()
        print("协程运行完..")
        print("当前时间：", time.ctime())

