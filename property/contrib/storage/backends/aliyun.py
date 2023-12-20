import os
import six
import logging
import datetime
import posixpath
from urllib.parse import urljoin

from django.conf import settings
from django.core.files import File
from django.utils.encoding import force_text, filepath_to_uri, force_bytes

from django.core.exceptions import ImproperlyConfigured, SuspiciousOperation
from django.core.files.storage import Storage

from oss2.api import _normalize_endpoint
from oss2 import Auth, Service, BucketIterator, Bucket, ObjectIterator
from oss2.exceptions import AccessDenied

logger = logging.getLogger("django")


class AliyunOperationError(Exception):
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)


class BucketOperationMixin(object):
    def _get_bucket(self, auth):
        if self.cname:
            return Bucket(auth, self.cname, self.bucket_name, is_cname=True)
        else:
            return Bucket(auth, self.end_point, self.bucket_name)

    def _list_bucket(self, service):
        return [bucket.name for bucket in BucketIterator(service)]

    def _create_bucket(self, auth):
        bucket = self._get_bucket(auth)
        bucket.create_bucket(settings.ALIYUN_OSS_BUCKET_ACL_TYPE)
        return bucket

    def _check_bucket_acl(self, bucket):
        if bucket.get_bucket_acl().acl != settings.ALIYUN_OSS_BUCKET_ACL_TYPE:
            bucket.put_bucket_acl(settings.ALIYUN_OSS_BUCKET_ACL_TYPE)
        return bucket


class AliyunBaseStorage(BucketOperationMixin, Storage):
    """
        Aliyun OSS2 Storage
        Ref:
            https://yshblog.com/blog/172
            https://github.com/xiewenya/django-aliyun-oss2-storage
            https://github.com/aliyun/django-oss-storage
    """
    location = ""

    def __init__(self):
        self.access_key_id = self._get_config('ALIYUN_OSS_ACCESS_KEY_ID')
        self.access_key_secret = self._get_config('ALIYUN_OSS_ACCESS_KEY_SECRET')
        self.end_point = _normalize_endpoint(self._get_config('ALIYUN_OSS_END_POINT').strip())
        self.bucket_name = self._get_config('ALIYUN_OSS_BUCKET_NAME')
        self.cname = self._get_config('ALIYUN_OSS_CNAME')

        self.auth = Auth(self.access_key_id, self.access_key_secret)
        self.service = Service(self.auth, self.end_point)

        try:
            if self.bucket_name not in self._list_bucket(self.service):
                # create bucket if not exists
                self.bucket = self._create_bucket(self.auth)
            else:
                # change bucket acl if not consists
                self.bucket = self._check_bucket_acl(self._get_bucket(self.auth))
        except AccessDenied:
            # 当启用了RAM访问策略，是不允许list和create bucket的
            self.bucket = self._get_bucket(self.auth)

    def _get_config(self, name):
        """
        Get configuration variable from environment variable
        or django setting.py
        """
        config = os.environ.get(name, getattr(settings, name, None))
        if config is not None:
            if isinstance(config, six.string_types):
                return config.strip()
            else:
                return config
        else:
            raise ImproperlyConfigured(
                "Can't find config for '%s' either in environment "
                "variable or in setting.py" % name)

    def _clean_name(self, name):
        """
        Cleans the name so that Windows style paths work
        """
        # Normalize Windows style paths
        clean_name = posixpath.normpath(name).replace('\\', '/')

        # os.path.normpath() can strip trailing slashes so we implement
        # a workaround here.
        if name.endswith('/') and not clean_name.endswith('/'):
            # Add a trailing slash as it was stripped.
            return clean_name + '/'
        else:
            return clean_name

    def _normalize_name(self, name):
        """
        Normalizes the name so that paths like /path/to/ignored/../foo.txt
        work. We check to make sure that the path pointed to is not outside
        the directory specified by the LOCATION setting.
        """

        base_path = force_text(self.location)
        base_path = base_path.rstrip('/')

        final_path = urljoin(base_path.rstrip('/') + "/", name)

        base_path_len = len(base_path)
        if (not final_path.startswith(base_path) or
                final_path[base_path_len:base_path_len + 1] not in ('', '/')):
            raise SuspiciousOperation("Attempted access to '%s' denied." %
                                      name)
        return final_path.lstrip('/')

    def _get_target_name(self, name):
        name = self._normalize_name(self._clean_name(name))
        if six.PY2:
            name = name.encode('utf-8')
        return name

    def _open(self, name, mode='rb'):
        print(f'HHHHHHHHHHHHHHH name: {name}')
        return AliyunFile(name, self, mode)

    def _save(self, name, content):
        source_filename = str(content)
        # 为保证django行为的一致性，保存文件时，应该返回相对于`media path`的相对路径。
        target_name = self._get_target_name(name)

        # Set header
        headers = {
            'Content-Type': 'application/octet-stream',
            'Content-Disposition': 'attachment; filename=%s' % os.path.basename(name)
        }

        with open(source_filename, "rb") as fp:
            data = fp.read()
            result = self.bucket.put_object(target_name, data, headers=headers)

            status_code = result.status     # HTTP返回码
            request_id = result.request_id  # 请求ID, 请求ID是本次请求的唯一标识，强烈建议在程序日志中添加此参数
            etag = result.etag              # ETag是put_object方法返回值特有的属性，用于标识一个Object的内容
            resp_headers = result.headers   # HTTP响应头部

            cls_name = self.__class__.__name__
            log_args = (cls_name, status_code, request_id, etag, resp_headers)
            logger.info("%s._save => status:%s, request_id:%s,etag:%s, resp_headers:%s", *log_args)

            if status_code != 200:
                raise AliyunOperationError(f'{cls_name} put file: `{source_filename}` ro AliCloud error!')

        # content.open()
        # content_str = b''.join(chunk for chunk in content.chunks())
        # self.bucket.put_object(target_name, content_str, headers=headers)
        # content.close()

        return self._clean_name(name)

    def get_file_header(self, name):
        name = self._get_target_name(name)
        return self.bucket.head_object(name)

    def exists(self, name):
        return self.bucket.object_exists(name)

    def size(self, name):
        file_info = self.get_file_header(name)
        return file_info.content_length

    def modified_time(self, name):
        file_info = self.get_file_header(name)
        return datetime.datetime.fromtimestamp(file_info.last_modified)

    def listdir(self, name):
        name = self._normalize_name(self._clean_name(name))
        if name and name.endswith('/'):
            name = name[:-1]

        files = []
        dirs = set()

        for obj in ObjectIterator(self.bucket, prefix=name, delimiter='/'):
            if obj.is_prefix():
                dirs.add(obj.key)
            else:
                files.append(obj.key)

        return list(dirs), files

    def url(self, name):
        name = self._normalize_name(self._clean_name(name))
        # name = filepath_to_uri(name) # 这段会导致二次encode
        name = name.encode('utf8')
        # 做这个转化，是因为下面的_make_url会用urllib.quote转码，转码不支持unicode，会报错，在python2环境下。
        return self.bucket._make_url(self.bucket_name, name)

    def read(self, name):
        pass

    def delete(self, name):
        name = self._get_target_name(name)
        result = self.bucket.delete_object(name)
        if result.status >= 400:
            raise AliyunOperationError(result.resp)


class AliyunMediaStorage(AliyunBaseStorage):
    location = settings.MEDIA_URL


class AliyunStaticStorage(AliyunBaseStorage):
    location = settings.STATIC_URL


class AliyunFile(File):
    def __init__(self, name, storage, mode):
        self._storage = storage
        self._name = name[len(self._storage.location):]
        self._mode = mode
        self.file = six.BytesIO()
        self._is_dirty = False
        self._is_read = False
        super(AliyunFile, self).__init__(self.file, self._name)

    def read(self, num_bytes=None):
        if not self._is_read:
            content = self._storage.bucket.get_object(self._name)
            self.file = six.BytesIO(content.read())
            self._is_read = True

        if num_bytes is None:
            data = self.file.read()
        else:
            data = self.file.read(num_bytes)

        if 'b' in self._mode:
            return data
        else:
            return force_text(data)

    def write(self, content):
        if 'w' not in self._mode:
            raise AliyunOperationError("Operation write is not allowed.")

        self.file.write(force_bytes(content))
        self._is_dirty = True
        self._is_read = True

    def close(self):
        if self._is_dirty:
            self.file.seek(0)
            self._storage._save(self._name, self.file)
        self.file.close()
