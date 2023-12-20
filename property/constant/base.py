import enum


class EnumBase(enum.Enum):
    @classmethod
    def iterator(cls):
        return iter(cls._member_map_.values())
