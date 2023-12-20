import time
import asyncio
import multiprocessing
import concurrent.futures


# ************** 多进程 1 **************
# 方法一：启动一个子进程，在子进程中运行异步代码
async def hello(i):
    print("hello", i)
    await asyncio.sleep(1)


def strap(tx, rx):
    start_t = time.time()

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(hello(3))

    print("Process method1 Ts: %s" % (time.time() - start_t))


def method1_with_async_process():
    # 启动一个子线程，在子线程中运行异步代码
    p = multiprocessing.Process(target=strap, args=(1, 3))
    p.start()

    # 子进程和主进程不会相互干扰
    for i in range(10):
        print(i)
# ************** 多进程 1 **************


# @@@@@@@@@@@@@@@@@ 多进程 2 @@@@@@@@@@@@@@@@@
# 方法二：loop.run_in_executor(executor, func, *args)
def blocks(n):
    """阻塞任务"""
    time.sleep(n)
    return n ** 2


async def run_blocking_tasks(executor):
    loop = asyncio.get_event_loop()
    # 在进程池中执行阻塞任务
    blocking_tasks = [
        loop.run_in_executor(executor, blocks, i)
        for i in range(30)
    ]
    completed, pending = await asyncio.wait(blocking_tasks)
    results = [t.result() for t in completed]
    print(results)


def method2_with_async_process():
    start_t = time.time()

    # 创建进程池
    executor = concurrent.futures.ProcessPoolExecutor(max_workers=3)
    event_loop = asyncio.get_event_loop()
    try:
        event_loop.run_until_complete(run_blocking_tasks(executor))
    finally:
        event_loop.close()

    print("methodr Process Total Ts: %s" % (time.time() - start_t))
# @@@@@@@@@@@@@@@@@ 多进程 2 @@@@@@@@@@@@@@@@@


# ######################## 多进程 3 ########################
# 方法三：第三方库aiomultiprocess
# ######################## 多进程 3 ########################

if __name__ == "__main__":
    # method1_with_async_process()
    method2_with_async_process()


