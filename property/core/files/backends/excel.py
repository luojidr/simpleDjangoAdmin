"""
xlrd, xlrwt, openpyxl, xlwings, pandas等库操作Excel

 _____________________________________________________________________________________
|            | 可操作excel文件格式   |      |      |      |       |          |         |
|    库名    |______________________| 读取 | 写入  | 修改 | 保存  | 格式调整  | 插入图片 |
|            |  .xls    |   .xlsx  |      |      |      |       |          |         |
|____________|__________|__________|______|______|______|_______|__________|_________|
|    xlrd    |    ✔    |    ✔     |  ✔  |   ✖  |  ✖   |  ✖   |    ✖     |   ✖     |
|____________|__________|__________|______|______|______|_______|__________|_________|
|    xlwt    |    ✔    |    ✖     |  ✖   |  ✔  |  ✔   |  ✔   |    ✔     |   ✔    |
|____________|__________|__________|______|______|______|_______|__________|_________|
|  xluntils  |    ✔    |    ✖     |  ✖   |  ✔  |  ✔   |  ✔   |    ✖     |   ✖    |
|____________|_________|___________|______|______|______|_______|__________|________|
|  xlwings   |    ✔    |    ✔     |  ✔  |   ✔  |  ✔  |  ✔   |    ✔     |   ✔    |
|____________|__________|__________|______|______|______|_______|__________|________|
| xlsxWriter |    ✖     |   ✔     |  ✖   |  ✔  |  ✖   |  ✔   |    ✔     |   ✔   |
|____________|__________|__________|______|______|______|_______|__________|________|
|  openpyxl  |    ✖     |   ✔     |  ✔  |   ✔  |  ✔  |  ✔   |    ✔     |   ✔    |
|____________|__________|__________|______|______|______|______|___________|________|
|   pandas   |    ✔    |    ✔     |  ✔  |   ✔  |  ✖   |  ✔  |    ✖     |   ✖    |
|____________|__________|__________|______|______|______|______|__________|_________|
注: xlrd2.0.1之后不支持.xlsx文件
"""

import json
import datetime
import os.path
from functools import partial

import csv
import xlwt         # xls
import xlsxwriter   # xlsx

__all__ = ["ExcelWriter"]


class ExcelMixin:
    def __init__(self, filename, headers=()):
        self.filename = filename
        self.headers = headers or []

        self.rows = 0
        self._set_headers()
        self._is_closed = False

    def _set_headers(self):
        if isinstance(self.headers, (list, tuple)):
            if not self.headers:
                return

            if all([isinstance(s, (bytes, str)) for s in self.headers]):
                self.write(self.headers)
                return

        raise ValueError("Row headers must string with each entry of list or tuple")

    def _parse_value(self, value):
        opts = {}

        if isinstance(value, (int, float)):
            value = str(value)
        elif isinstance(value, datetime.datetime):
            value = value.strftime("%Y-%m-%d %H:%M:%S")
        elif isinstance(value, datetime.date):
            value = value.strftime("%Y-%m-%d")
        elif isinstance(value, dict):
            is_img = value.get("type") == "img"
            opts = dict(is_img=is_img, options=value.get("options") or {})
            value = value["filename"] if is_img else json.dumps(value)

        return value, opts

    def _get_values(self, values):
        if not isinstance(values[0], (list, tuple)):
            nest_values = [values]
        else:
            nest_values = values

        return nest_values

    def write(self, values, skip_row=0):
        """ one row by one row to write xls or xlsx
            insert image:
                [{"type": "img", "filename": "/tmp/images/xxxx.png"}, "Test", 12345]
        """
        values = self._get_values(values)

        for row_values in values:
            for column, value in enumerate(row_values):
                value, opts = self._parse_value(value)
                is_img = opts.pop("is_img", False)
                options = opts.pop("options", {})

                if is_img:
                    self.set_cell(self.rows, column, options=options)
                    self.insert_image(self.rows, column, value, options=None)
                else:
                    self._worksheet.write(self.rows, column, value)

            self.rows += 1 + skip_row

    def insert_image(self, row, col, filename, options=None):
        """ insert image """

    def set_cell(self, row, col, width=35, height=200, options=None):
        """ set excel cell width and height """

    def close(self):
        if not self._is_closed:
            self._workbook.close()
            self._is_closed = True


class CSVWriter(ExcelMixin):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        fp = open(self.filename, "w", newline="")
        self._workbook = csv.writer(fp)
        self._workbook.close = partial(lambda f: f.close(), fp)

    def write(self, values, skip_row=0):
        # csv values is list or tuple
        self._workbook.writerows(values)


class XlsWriter(ExcelMixin):
    MAX_ROW_INDEX = 65535

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._workbook = xlwt.Workbook(encoding='utf-8')
        self._worksheet = self._workbook.add_sheet(sheetname="Sheet 1")
        self._workbook.close = partial(self._workbook.save, self.filename)

    def write(self, values, skip_row=0):
        values = self._get_values(values)

        if len(self.headers) + len(values) > self.MAX_ROW_INDEX:
            raise ValueError("Row index was 65535, not allowed by .xls format")

        super().write(values, skip_row)

    def set_cell(self, row, col, width=35, height=200, options=None):
        self._worksheet.row(row).height = height
        self._worksheet.col(col).width = width

    def insert_image(self, row, col, filename, options=None):
        options = options or {}
        new_options = dict(
            x=options.get("x", 10), y=options.get("y", 10),
            scale_x=options.get("x_scale", 0.6), scale_y=options.get("y_scale", 0.6)
        )
        self._worksheet.insert_bitmap(filename, row, col, **new_options)


class XlsxWriter(ExcelMixin):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._workbook = xlsxwriter.Workbook(self.filename)
        self._worksheet = self._workbook.add_worksheet()

    def write(self, values, skip_row=0):
        super().write(values, skip_row)

    def set_cell(self, row, col, width=35, height=200, options=None):
        # width = options.get("x_scale", width)
        # height = options.get("y_scale", height)

        self._worksheet.set_row(row, height)
        self._worksheet.set_column(col, col, width)

    def insert_image(self, row, col, filename, options=None):
        options = options or {}
        new_options = dict(
            align="center",
            x_offset=options.get("x", 10), y_offset=options.get("y", 10),
            x_scale=options.get("x_scale", 0.6), y_scale=options.get("y_scale", 0.6),
        )
        self._worksheet.insert_image(row, col, filename, options=new_options)


class ExcelWriter:
    CSV = "csv"
    XLS = "xls"
    XLSX = "xlsx"

    def __init__(self, filename):
        self._writer = self.get_writer_factory(filename)

    def get_writer_factory(self, filename):
        _, ext = os.path.splitext(filename)
        ext = ext[1:].lower()

        assert ext in [self.CSV, self.XLS, self.XLSX], "file format error"

        if ext == self.CSV:
            writer_cls = CSVWriter
        elif ext == self.XLS:
            writer_cls = XlsWriter
        else:
            writer_cls = XlsxWriter

        return writer_cls(filename)

    def write(self, values, skip_row=0):
        self._writer.write(values, skip_row)

    def close(self):
        self._writer.close()

