import time
import asyncio
import aiohttp


async def main(url):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:

            # print("Status:", response.status)
            # print("Content-type:", response.headers['content-type'])

            # data = await response.json()
            data = await response.text()
            # print(data)

            return response.status == 200
        # and data.get("code") == 200


def get_task_list(nums):
    url_1 = "https://cuth.com/circle/circle?page=1&size=10&user=3070&tagId=38"
    # url_2 = "https://cuth.com/user/messageCount/3070"

    task_list = [asyncio.ensure_future(main(url_1)) for i in range(nums)]
    # task_list.extend([asyncio.ensure_future(main(url_2)) for i in range(nums)])

    return task_list


if __name__ == "__main__":
    # asyncio.run(main())

    # *****************************
    start_t = time.time()
    nums = 600
    loop = asyncio.get_event_loop()

    # task_list = [asyncio.ensure_future(main()) for i in range(nums)]
    task_list = get_task_list(nums)

    rets = loop.run_until_complete(asyncio.gather(*task_list))
    loop.close()

    total_seconds = time.time() - start_t
    total_cnt = len(rets)
    ok_cnt = len([f for f in rets if f])
    fail_cnt = total_cnt - ok_cnt
    print("Wait total_seconds: %.2f, ok_cnt: %s, fail_cnt: %s, qps: %.2f, R: %.2fms/request" % (
        total_seconds, ok_cnt, fail_cnt, total_cnt / total_seconds, total_seconds * 1000 / total_cnt
    ))
