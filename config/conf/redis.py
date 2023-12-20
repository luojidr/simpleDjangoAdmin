from django.conf import settings


class RedisSharedConfig(object):
    """ Redis 集群配置 """
    REDIS_STARTUP_NODES = [
        {"host": "192.168.190.128", "port": "6380"},
        {"host": "192.168.190.128", "port": "6381"},
        {"host": "192.168.190.128", "port": "6382"},
        {"host": "192.168.190.128", "port": "6383"},
        {"host": "192.168.190.128", "port": "6384"},
        {"host": "192.168.190.128", "port": "6385"},
    ]

    REDIS_DECODE_RESPONSES = True


class RedisBloomConfig(object):
    """ 布隆过滤器的Redis配置 """
    REDIS_HOST = "192.168.190.128"
    REDIS_PORT = 6380
    REDIS_DB = 0
    REDIS_PASSWORD = ""

