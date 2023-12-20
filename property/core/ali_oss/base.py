from aliyunsdkcore.client import AcsClient

from config.conf import aliyun


class AliOssBase(object):
    ACCEPT_FORMAT = "json"
    PROTOCOL_TYPE = "https"  # https | http
    DEFAULT_REGION_ID = "cn-hangzhou"

    def __init__(self,
                 region_id=DEFAULT_REGION_ID,
                 access_key_id=None,
                 access_key_secret=None,
                 **kwargs
                 ):
        self._region_id = region_id
        self._access_key_id = access_key_id or self.conf.ACCESS_KEY_ID
        self._access_key_secret = access_key_secret or self.conf.ACCESS_KEY_SECRET

        self._client = AcsClient(self._access_key_id, self._access_key_secret, self._region_id, **kwargs)

    @property
    def conf(self):
        return aliyun.AliConfig()
