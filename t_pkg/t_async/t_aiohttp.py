import asyncio
import inspect
import aiohttp

loop = asyncio.get_event_loop()


async def fetch(url):
    async with aiohttp.ClientSession(loop=loop) as session:
        async with session.get(url) as resp:
            response = await resp.read()
            return response


async def async_function():
    return 1


async def coroutine_test():
    await asyncio.sleep(1)


def simple_coroutine():
    print('-> coroutine started')
    x = yield
    print('-> coroutine received: ', x)


if __name__ == "__main__":
    coroutine = async_function()
    print(coroutine, type(coroutine))
    print(dir(coroutine))

    try:
        coroutine.send(None)
    except StopIteration as e:
        print("StopIteration:", e.value)

    gen = simple_coroutine()
    gen_status = inspect.getgeneratorstate(gen)
    print("gen_status:", gen_status)

    cor = coroutine_test()
    cor_status = inspect.getcoroutinestate(cor)
    print("cor_status:", cor_status)

