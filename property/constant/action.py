from .base import EnumBase


class ApiActionEnum(EnumBase):
    CREATE = (1, "create")
    UPDATE = (2, "update")
    DELETE = (3, "delete")

    @property
    def type(self):
        return self.value[0]

    @property
    def action(self):
        return self.value[1]

