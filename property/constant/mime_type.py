import enum

from .base import EnumBase


class BaseEnum(EnumBase):
    @property
    def type(self):
        return self.value[0]

    @property
    def fmt(self):
        return self.value[1]

    @classmethod
    def get_choices(cls):
        return [(e.type, e.fmt) for e in cls.iterator()]


@enum.unique
class MimeTypeEnum(BaseEnum):
    GE = (0, "application/octet-stream")
    JPEG = (1, "image/jpeg")
    PNG = (2, "image/png")
    PDF = (3, "application/pdf")
    DOC = (4, "doc")
    DOCX = (5, "docx")




