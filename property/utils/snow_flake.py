"""
Snowflake algorithm implement of python:
Twitter's Snowflake algorithm implementation which is used to generate distributed IDs.
https://github.com/twitter-archive/snowflake/blob/snowflake-2010

snowflake 算法说明:
    Reference: https://www.cnblogs.com/oklizz/p/11865750.html

    snowflake 算法是twitter开源的分布式id生成算法，采用Scala语言实现，是把一个64位的long型的id，1个bit是不用的，
    用其中的41 bit作为毫秒数，用10 bit作为工作机器id，12 bit作为序列号。

    (1): 1 bit: 不用，为啥呢？因为二进制里第一个bit为如果是1，那么都是负数，但是我们生成的id都是正数，
         所以第一个bit统一都是 0。

    (2): 41 bit: 表示的是时间戳，单位是毫秒。41 bit可以表示的数字多达 2^41 - 1，也就是可以标识 2^41 - 1个毫秒值，
         换算成年就是表示69年的时间。

    (3): 10 bit: 记录工作机器id，代表的是这个服务最多可以部署在 2^10台机器上哪，也就是1024台机器。
        但是 10 bit里 5个 bit 代表机房 id，5个bit代表机器id。意思就是最多代表 2^5个机房（32个机房），
        每个机房里可以代表 2^5 个机器（32台机器）。

    (4): 12 bit: 这个是用来记录同一个毫秒内产生的不同 id，12 bit可以代表的最大正整数是 2^12 - 1 = 4096，
         12 bit 代表的数字来区分同一个毫秒内的 4096 个不同的 id。

    0 | 0001100 10100010 10111110 10001001 01011100 00 | 10001 | 1 1001 | 0000 00000000
"""

import os
import time
import random
import logging
import threading
from multiprocessing.dummy import Pool as ThreadPool
from concurrent import futures
from concurrent.futures import ThreadPoolExecutor, wait


class InvalidSystemClock(Exception):
    """ Clock callback exception """


class Snowflake(object):
    # 64位ID的划分
    DATA_CENTER_ID_BITS = 5     # 5 bit 代表机房id，或数据中心id
    WORKER_ID_BITS = 5          # 5 bit 代表机器id
    SEQUENCE_BITS = 12          # 12 bit 同一个毫秒内产生的不同 id

    # 最大取值计算
    MAX_WORKER_ID = -1 ^ (-1 << WORKER_ID_BITS)
    MAX_DATA_CENTER_ID = -1 ^ (-1 << DATA_CENTER_ID_BITS)

    # 移位偏移计算
    WORKER_ID_SHIFT = SEQUENCE_BITS
    DATA_CENTER_ID_SHIFT = SEQUENCE_BITS + WORKER_ID_BITS
    TIMESTAMP_LEFT_SHIFT = SEQUENCE_BITS + WORKER_ID_BITS + DATA_CENTER_ID_BITS

    # 序号循环掩码
    SEQUENCE_MASK = -1 ^ (-1 << SEQUENCE_BITS)

    # Twitter元年时间戳
    TW_EPOCH = 1288834974657

    CLS_LOCK = threading.Lock()

    def __init_instance(self, data_center_id=None, worker_id=None, did_wid=-1, sequence=0):
        """
        初始化
        :param data_center_id: 数据中心（机器区域）ID
        :param worker_id: 机器ID
        :param did_wid: 数据中心和机器id合成10位二进制，用十进制0-1023表示，通过算法会拆分成 data_center_id 和 worker_id
        :param sequence: 起始序号
        """
        if did_wid > 0:
            data_center_id = did_wid >> 5
            worker_id = did_wid ^ (data_center_id << 5)

        # sanity check
        if worker_id and (worker_id > self.MAX_WORKER_ID or worker_id < 0):
            raise ValueError('worker_id值越界')

        if data_center_id and (data_center_id > self.MAX_DATA_CENTER_ID or data_center_id < 0):
            raise ValueError('datacenter_id值越界')

        self.data_center_id = data_center_id or random.randint(0, self.MAX_DATA_CENTER_ID)
        self.worker_id = worker_id or random.randint(0, self.MAX_WORKER_ID)

        self.sequence = sequence
        self.last_timestamp = self._gen_timestamp()  # 上次计算的时间戳

    def __new__(cls, *args, **kwargs):
        """ 单例模式, 每次实例化时，实例的属性相同(注意) """
        if not hasattr(cls, "_instance"):
            # cls._instance = object.__new__(cls, *args, **kwargs)
            cls._instance = super(Snowflake, cls).__new__(cls)

            # Important:
            # (1): lock 锁可以此处定义，也可以在 __init_instance 中定义
            # (2): 若不在此处实例化属性，即使是同一个实例也会每次均会实例化，造成属性相同，雪花算法有重复
            cls._instance.lock = threading.Lock()
            cls._instance.__init_instance(*args, **kwargs)

        return cls._instance

    def _gen_timestamp(self):
        """
        生成整数时间戳
        :return:int timestamp
        """
        return int(time.time() * 1000)

    def _til_next_millis(self, last_timestamp):
        """ 等到下一毫秒 """
        timestamp = self._gen_timestamp()
        while timestamp <= last_timestamp:
            timestamp = self._gen_timestamp()

        return timestamp

    def get_id(self, *args, **kw):
        """
        获取雪花算法 ID，重复率为: 0
        经多线程粗略测试计算， QPS: 155000 req/s, 155 req/ms, QPS 完全够用
        """
        with self.lock:
            timestamp = self._gen_timestamp()

            # 时钟回拨
            if timestamp < self.last_timestamp:
                logging.error('clock is moving backwards. Rejecting requests until {}'.format(self.last_timestamp))
                raise InvalidSystemClock

            if timestamp == self.last_timestamp:
                self.sequence = (self.sequence + 1) & self.SEQUENCE_MASK

                if self.sequence == 0:
                    timestamp = self._til_next_millis(self.last_timestamp)
            else:
                self.sequence = 0

            self.last_timestamp = timestamp

            uid = ((timestamp - self.TW_EPOCH) << self.TIMESTAMP_LEFT_SHIFT) | \
                  (self.data_center_id << self.DATA_CENTER_ID_SHIFT) | \
                  (self.worker_id << self.WORKER_ID_SHIFT) | self.sequence

            return uid


def test_by_ThreadPool():
    """ from multiprocessing.dummy import Pool as ThreadPool
    本机一千万测试结果如下:
        ThreadPool: 10000000
        ThreadPool: 10000000
        ThreadPool: True
        ThreadPool 重复率: 0.0 50.464980602264404
    """
    concurrency_max = 10000000
    start_time = time.time()

    pool = ThreadPool()
    ret = pool.map(Snowflake(1, 2).get_id, range(concurrency_max))
    pool.close()
    pool.join()

    end_time = time.time()

    print("ThreadPool:", len(ret))
    print("ThreadPool:", len(set(ret)))
    print("ThreadPool:", len(set(ret)) == concurrency_max)
    print("ThreadPool 重复率:", (len(ret) - len(set(ret))) * 1.0 / len(ret) * 100, end_time - start_time)


def test_by_ThreadPoolExecutor():
    """ 使用 concurrent.futures
    本机一百万测试结果如下:

    future_list = [executor.submit(Snowflake(2, 3).get_id) for i in range(concurrency_max)]

    (1): executor.map
        gen = executor.map(Snowflake(2, 3).get_id, range(concurrency_max))
        result = list(gen)

        ThreadPoolExecutor: 1000000
        ThreadPoolExecutor: 1000000
        ThreadPoolExecutor: True
        ThreadPoolExecutor 重复率: 0.0 60.61892819404602

    (2): wait
        ret_futures = wait(future_list)
        done_result = [f.result() for f in ret_futures.done]
        # not_done_result = [nf.result() for nf in ret_futures.not_done]
        result = done_result

        ThreadPoolExecutor: 1000000
        ThreadPoolExecutor: 1000000
        ThreadPoolExecutor: True
        ThreadPoolExecutor 重复率: 0.0 59.86428761482239

    (3): futures.as_completed
        result = [future.result() for future in futures.as_completed(future_list)]

        ThreadPoolExecutor: 1000000
        ThreadPoolExecutor: 1000000
        ThreadPoolExecutor: True
        ThreadPoolExecutor 重复率: 0.0 59.72651958465576
    """
    concurrency_max = 1000000
    start_time = time.time()

    with ThreadPoolExecutor(max_workers=os.cpu_count()) as executor:
        # # Two Method: map [结果生成器]
        # gen = executor.map(Snowflake(2, 3).get_id, range(concurrency_max))
        # result = list(gen)

        future_list = [executor.submit(Snowflake(2, 3).get_id) for i in range(concurrency_max)]

        # Two Method: wait
        # ret_futures = wait(future_list)
        # done_result = [f.result() for f in ret_futures.done]
        # # not_done_result = [nf.result() for nf in ret_futures.not_done]
        # result = done_result

        # Three Method
        result = [future.result() for future in futures.as_completed(future_list)]

    end_time = time.time()

    print("ThreadPoolExecutor:", len(result))
    print("ThreadPoolExecutor:", len(set(result)))
    print("ThreadPoolExecutor:", len(set(result)) == concurrency_max)
    print("ThreadPoolExecutor 重复率:", (len(result) - len(set(result))) * 1.0 / len(result) * 100, end_time - start_time)


if __name__ == "__main__":
    # test_by_ThreadPool()
    test_by_ThreadPoolExecutor()

