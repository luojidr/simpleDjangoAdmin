import os.path

from fosun_circle.constants.enums.content_type import ContentTypeEnum


class FileWrapper:
    """ Wrapper to convert file-like objects to iterables
        from wsgiref.util import FileWrapper
    """

    def __init__(self, filename, block_size=None):
        self.filename = filename
        self._block_size = int(block_size)
        self._file_like = open(filename, "rb")

        _, ext = os.path.splitext(filename.lower())
        self.file_ext = ext[1:] if ext.startswith(".") else ext

    def _get_size(self):
        if not hasattr(self, "_size"):
            pos = self._file_like.tell()
            self._file_like.seek(0, os.SEEK_END)
            self._size = self._file_like.tell()
            self._file_like.seek(pos)

            return self._size

        return self._size

    size = property(_get_size)

    @property
    def content_type(self):
        for one_enum in ContentTypeEnum.iterator():
            suffix = one_enum.suffix
            content_type = one_enum.content_type

            if self.file_ext == suffix:
                return content_type

        return 'application/octet-stream'

    def read(self, n=None):
        if n is None:
            return self._file_like.read()

        return self._file_like.read(n)

    def iter_read(self):
        if self._block_size is None:
            return self._file_like.read()

        while True:
            content = self._file_like.read(self._block_size)
            if content:
                yield content
            else:
                break

    def __iter__(self):
        return self

    def __next__(self):
        data = self._file_like.read(self._block_size)
        if data:
            return data

        raise StopIteration

    def close(self):
        if not self._file_like.closed:
            self._file_like.close()

        if os.path.exists(self.filename):
            os.remove(self.filename)

    def __del__(self):
        self.close()
