import datetime
import heapq
import types
import time
import asyncio



class Task(object):
    """相当于asyncio.Task，存储协程和要执行的时间"""

    def __init__(self, wait_until, coro):
        self.coro = coro
        self.waiting_until = wait_until

    def __eq__(self, other):
        return self.waiting_until == other.waiting_until

    def __lt__(self, other):
        return self.waiting_until < other.waiting_until


class SleepLoop(object):
    """一个事件循环，每次执行最先需要执行的协程，时间没到就阻塞等待，相当于asyncio中的事件循环"""

    def __init__(self, *coro):
        self._new = coro
        self._waiting = []

    def run_until_complete(self):
        # 启动所有协程
        for coro in self._new:
            print(coro)
            wait_for = coro.send(None)
            heapq.heappush(self._waiting, Task(wait_for, coro))

        # 保持运行，直到没有其他事情要做
        while self._waiting:
            now = datetime.datetime.now()

            # 每次取出最先执行的协程
            task = heapq.heappop(self._waiting)
            if now < task.waiting_until:
                delta = task.waiting_until - now
                time.sleep(delta.total_seconds())
                print(task.coro, delta.total_seconds())
                now = datetime.datetime.now()

            try:
                # 恢复不需要等待的协程
                wait_until = task.coro.send(now)
                heapq.heappush(self._waiting, Task(wait_until, task.coro))
            except StopIteration:
                # 捕捉协程结束的抛出异常
                pass


# @types.coroutine
@asyncio.coroutine
def sleep(seconds):
    """暂停一个协程指定时间，可把他当做asyncio.sleep()"""
    now = datetime.datetime.now()
    wait_until = now + datetime.timedelta(seconds=seconds)
    actual = yield wait_until

    return actual - now if actual else datetime.timedelta(seconds=0)


async def countdown(label, length, *, delay=0):
    """协程函数，实现具体的任务"""
    print(label, "waiting", delay, "seconds before starting countdown")
    delta = await sleep(delay)
    print(label, 'starting after waiting', delta)

    while length:
        print(label, "T-minus", length)
        waited = await sleep(1)
        length -= 1

    print(label, 'lift-off!')


def main():
    """启动事件循环，运行三个协程"""
    loop = SleepLoop(
        countdown('A', 5),
        countdown('B', 3, delay=4),
        countdown('C', 4, delay=2)
    )
    start = datetime.datetime.now()
    loop.run_until_complete()
    print('Total elapsed time is', datetime.datetime.now() - start)


if __name__ == "__main__":
    main()
    asyncio.shield()

