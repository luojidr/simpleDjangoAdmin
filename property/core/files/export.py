import os.path

from django.utils.encoding import escape_uri_path
from django.http.response import Http404, HttpResponse
from django.http.response import StreamingHttpResponse, FileResponse

from .base import FileWrapper
from .backends import excel

__all__ = ["FileExport"]


class FileExport:
    CHUNK_SIZE = 1 << 20        # 1Mb
    MAX_STREAM_SIZE = 5 << 20   # 5Mb

    def __init__(self, filename, attachment_name=None):
        self._filename = filename
        self._attachment_name = attachment_name

        self._is_write = False

    @property
    def attachment_name(self):
        if self._attachment_name is not None:
            file_ext = "." + self.file_wrapper.file_ext

            if not self._attachment_name.endswith(file_ext):
                name = self._attachment_name + file_ext
            else:
                name = self._attachment_name
        else:
            name = self.file_wrapper.filename

        self._attachment_name = os.path.basename(name)
        return self._attachment_name

    @property
    def file_wrapper(self):
        wrapper = getattr(self, "_file_wrapper", None)

        if wrapper is None:
            if not os.path.exists(self._filename):
                # raise FileExistsError("Path<%s> Not Exist" % self._filename)
                wrapper = None
            else:
                wrapper = FileWrapper(filename=self._filename, block_size=self.CHUNK_SIZE / 2)

            setattr(self, "_file_wrapper", wrapper)
            return wrapper

        return wrapper

    def write_data(self, values):
        writer = excel.ExcelWriter(filename=self._filename)
        writer.write(values)
        writer.close()

        self._is_write = True

    def make_response(self, values=None):
        values = values or []

        if not self._is_write and len(values) > 0:
            self.write_data(values=values)

        if not self._is_write and not os.path.exists(self._filename):
            raise RuntimeError("Must write the data first!")

        if self.file_wrapper is None:
            raise FileExistsError("File not exist")

        file_size = self.file_wrapper.size

        if file_size <= self.CHUNK_SIZE:
            response = HttpResponse(content=self.file_wrapper.read())
        elif file_size <= self.MAX_STREAM_SIZE * 2:
            if file_size <= self.MAX_STREAM_SIZE:
                response = StreamingHttpResponse(self.file_wrapper.iter_read())
            else:
                response = StreamingHttpResponse(self.file_wrapper)
        else:
            response = FileResponse(self.file_wrapper)

        response['Content-Length'] = file_size
        response['Content-type'] = self.file_wrapper.content_type

        filename = escape_uri_path(self.attachment_name)
        response['Content-Disposition'] = "attachment; filename*=UTF-8''{}".format(filename)

        return response

