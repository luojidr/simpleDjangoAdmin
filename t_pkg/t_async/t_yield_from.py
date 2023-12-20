from collections.abc import Iterable, Iterator, Generator
from inspect import getgeneratorstate, isgeneratorfunction


def gen_one():
    subgen = range(10)
    yield from subgen


def gen_two():
    # subgen = range(2)
    # for item in subgen:
    #     yield item
    yield 1
    yield 2
    # return 3


def gen():
    yield from subgen()


def subgen():
    while 1:
        x = yield
        yield x + 1


def main():
    g = gen()

    # next(g)                 # 驱动生成器g开始执行到第一个 yield
    for i in range(10):
        next(g)
        retval = g.send(i)     # 看似向生成器 gen() 发送数据
        print(i, retval)           # 返回2
    # # g.throw(StopIteration)  # 看似向gen()抛入异常


def simple_yield1(a):
    print("-> Started:a =", a)
    b = yield a
    print("-> Received:b =", b)
    c = yield b + a
    print("-> Received:c =", c)
    return c


def simple_yield2():
    print("-> Started: simple_yield2")
    yield
    print("-> End: simple_yield2")


def simple_yield_from():
    val = yield from simple_yield1(10)
    print("jjjjj:", val)
    return val


from collections import namedtuple

Result = namedtuple('Result', 'count average')


def get_average():
    """ 子生成器 """
    total = 0.0
    count = 0
    average = None

    while True:
        # send 发送值给yield接收, yield 后面可以没有参数；
        # 有参数时 yield average 是为了让调用方迭代获取a值，和 term 没有关系
        term = yield average
        if term is None:
            break
        total += term
        count += 1
        average = total / count

    return Result(count, average)


def delegate_gen(results, key):
    """ 委托生成器 """
    # while True:
        # 只有当生成器 get_average()结束，才会返回结果给results赋值
    results[key] = yield from get_average()        # 无 while True 抛 StopIteration
    print("grouper end")

    return results    # 有无 while True 都会抛 StopIteration


def call_main(data):
    """ 调用方 """
    results = {}
    for key, values in data.items():
        delegation = delegate_gen(results, key)
        next(delegation)    # 启动/激活子生成器，第一次运行到 yield 阻塞暂停

        for value in values:
            delegation.send(value)
        delegation.send(None)   # 结束子生成器(return 了)

    report(results)


#如果不使用yield from，仅仅通过yield实现相同的效果，如下：
def main2(data):
    for key, values in data.items():
        aver = get_average()
        next(aver)
        for value in values:
            aver.send(value)
        try: #通过异常接受返回的数据
            aver.send(None)
        except Exception as e:
            result = e.value
            print(result)


def report(results):
    for key, result in sorted(results.items()):
        group, unit = key.split(';')
        print('{:2} {:5} averaging {:.2f} {}'.format(result.count, group, result.average, unit))



if __name__ == "__main__":
    # # 嵌套生成器不必通过循环迭代yield，而是直接yield from。以下两种在生成器里玩子生成器的方式是等价的
    # one = list(gen_one())
    # two = list(gen_two())
    #
    # print(one)
    # print(two)
    #
    # # 功能就是在子生成器和原生成器的调用者之间打开双向通道，两者可以直接通信
    # main()

    # simple_yield1
    # sy = simple_yield1(14)
    # next(sy)
    # sy.send(10)
    # try:
    #     sy.send(121)
    # except StopIteration as e:
    #     print("DDD:", e.value)

    # gen_yield_from = simple_yield_from()
    # next(gen_yield_from)
    # gen_yield_from.send(21)
    # gen_yield_from.send(213)

    data = {
        # 'girls;kg': [40.9, 38.5, 44.3, 42.2, 45.2, 41.7, 44.5, 38.0, 40.6, 44.5],
        # 'girls;m': [1.6, 1.51, 1.4, 1.3, 1.41, 1.39, 1.33, 1.46, 1.45, 1.43],
        # 'boys;kg': [39.0, 40.8, 43.2, 40.8, 43.1, 38.6, 41.4, 40.6, 36.3],
        'boys;m': [1.38, 1.5, 1.32, 1.25, 1.37, 1.48, 1.25, 1.49, 1.46],
    }
    call_main(data)

    # for it in gen_two():
    #     print(it)

    # def mygen(n):
    #     now = 0
    #     while now < n:
    #         r = yield now
    #         print("r:", r)
    #         now += 1
    #
    # gen = mygen(2)
    # print("1:", getgeneratorstate(gen))
    #
    # print(next(gen))
    # print(gen.send(200))
    # print("2:", getgeneratorstate(gen))
    #
    # gen.close()
    # print("3:", getgeneratorstate(gen))




