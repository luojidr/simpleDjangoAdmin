import asyncio
import time
from threading import Thread
import concurrent.futures


async def hello(i):
    st = time.time()
    await asyncio.sleep(i)
    print("hello: %s, Ts:%s" % (i, time.time() - st))
    return i


async def main():
    tasks = [asyncio.create_task(hello(i)) for i in range(30)]
    await asyncio.gather(*tasks)


# ************** 多线程 1 **************
# 方法一：启动一个子线程，在子线程中运行异步代码
def async_main():
    start_t = time.time()

    asyncio.run(main())

    print("method1 Total Ts: %s" % (time.time() - start_t))


def method1_with_async_thread():
    # 在子线程中运行异步任务
    t = Thread(target=async_main)
    t.start()

    # 不会干扰主线程
    for i in range(3):
        print(i)
# ************** 多线程 1 **************


# @@@@@@@@@@@@@@@@@ 多线程 2 @@@@@@@@@@@@@@@@@
# 方法二：loop.call_soon_threadsafe()函数
# loop.call_soon()              用于注册回调，当异步任务执行完成时会在当前线程按顺序执行注册的普通函数
# loop.call_soon_threadsafe()   用于在一个线程中注册回调函数，在另一个线程中执行注册的普通函数
# asyncio.run_coroutine_threadsafe()函数则是异步执行回调函数，传入写成函数
def start_loop(loop):
    start_t = time.time()

    asyncio.set_event_loop(loop)
    loop.run_until_complete(main())

    print("method2 Total Ts: %s" % (time.time() - start_t))


def more_work(x):
    print('More work {}'.format(x))
    time.sleep(x)
    print('Finished more work {}'.format(x))


def method2_with_async_thread():
    # 在主线程创建事件循环，并在另一个线程中启动
    start_t = time.time()
    new_loop = asyncio.new_event_loop()
    t = Thread(target=start_loop, args=(new_loop, ))
    t.start()

    # 在主线程中注册回调函数，在子线程中按顺序执行回调函数
    new_loop.call_soon_threadsafe(more_work, 1)
    new_loop.call_soon_threadsafe(more_work, 3)

    # 不会阻塞主线程
    for i in range(10):
        print(i)

    # print("method2 Main Ts: %s" % (time.time() - start_t))


def method3_with_async_thread():
    # 在主线程创建事件循环，并在另一个线程中启动
    new_loop = asyncio.new_event_loop()
    t = Thread(target=start_loop, args=(new_loop,))
    t.start()

    # 在主线程中注册回调协程函数，在子线程中按异步执行回调函数
    asyncio.run_coroutine_threadsafe(hello(3.5), new_loop)
    asyncio.run_coroutine_threadsafe(hello(1.5), new_loop)

    # 不会阻塞主线程
    for i in range(10):
        print(i)
# @@@@@@@@@@@@@@@@@ 多线程 2 @@@@@@@@@@@@@@@@@


# ######################## 多线程 4 ########################
# 方法四：loop.run_in_executor(executor, func, *args)
# loop.run_in_executor()函数用于在特定的executor中执行函数。
# executor参数必须是 concurrent.futures.Executor实例对象，传入None表示在默认的executor中执行。返回一个可等待的协程对象
def blocks(n):
    """阻塞任务"""
    time.sleep(n)
    return n ** 2


async def run_blocking_tasks(executor):
    loop = asyncio.get_event_loop()

    # 在线程池中执行阻塞任务
    blocking_tasks = [
        loop.run_in_executor(executor, blocks, i)
        for i in range(30)
    ]

    completed, pending = await asyncio.wait(blocking_tasks)
    results = [t.result() for t in completed]
    print(results)


def method4_with_async_thread():
    start_t = time.time()

    # 创建线程池
    executor = concurrent.futures.ThreadPoolExecutor(max_workers=3)
    event_loop = asyncio.get_event_loop()

    try:
        event_loop.run_until_complete(run_blocking_tasks(executor))
    finally:
        event_loop.close()

    print("method4 Total Ts: %s" % (time.time() - start_t))
# ######################## 多线程 4 ########################


if __name__ == "__main__":
    method1_with_async_thread()
    # method2_with_async_thread()
    # method3_with_async_thread()
    # method4_with_async_thread()
