import uuid
import time
import os.path

import oss2

from .base import AliOssBase
from .detector import AliScanDetector


class AliOssFileUpload(AliOssBase):
    """ OSS 文件上传 """

    UPLOAD_FILE_TYPE = {
        1: "图片",
        2: "文件",
        3: "视频",
        4: "语音"
    }

    IMAGE_SUFFIX_LIST = ("jpg", "jpeg", "png", "svg")

    def __init__(self, bucket_name=None, endpoint=None, **kwargs):
        """
        :param bucket_name: string, 文件存储的位置
        :param endpoint:    string,
        :param kwargs:      dict, key 或 secret
        """
        super(AliOssFileUpload, self).__init__(**kwargs)

        self._file_type = None
        self._bucket_name = bucket_name or self.conf.BUCKET_NAME
        self._endpoint = endpoint or self.conf.ENDPOINT
        self._bucket_key = kwargs.pop("bucket_key", None)

        auth = oss2.Auth(self._access_key_id, self._access_key_secret)
        self._bucket = oss2.Bucket(auth, self._endpoint, self._bucket_name)

    @property
    def bucket_key(self):
        if self._bucket_key is not None:
            return self._bucket_key

        _, ext = os.path.splitext(self.filename)

        if self._file_type == 1:
            if ext[1:].lower() in self.IMAGE_SUFFIX_LIST:
                bucket_key = self.conf.STD_BUCKET_KEY
            else:
                bucket_key = self.conf.NON_STD_BUCKET_KEY

        return bucket_key

    def _validate(self, file_bytes):
        """ 文本或文件反垃圾审查校验 """
        assert self._file_type in self.UPLOAD_FILE_TYPE, "文件上传类型错误！"

        detector = AliScanDetector()
        if self._file_type == 1 and not detector.detect_image(file_bytes):
            raise ValueError("文本或文件反垃圾审查未通过")

    def upload(self, filename, file_bytes, file_type=1):
        """ 上传文件
        :param filename:    string, 文件名
        :param file_bytes:  string, 文件字节数
        :param file_type:   int,    文件类型 1: 图片 2: 文件 3: 视频 4: 语音
        :return:
        """
        self._file_type = file_type
        self.filename = filename

        filename, ext = os.path.splitext(filename)
        unique_filename = filename + "_" + str(time.time() * 1000) + ext
        key = self.bucket_key + unique_filename

        result = self._bucket.put_object(key=key, data=file_bytes)




