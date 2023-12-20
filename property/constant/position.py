from .base import EnumBase


class MenuPositionEnum(EnumBase):
    FIRST = (0, "submenu-first")    # 父菜单的第一个菜单: 即首位
    PREV = (-1, "peer-prev")        # 同级(兄弟)菜单前一个
    NEXT = (1, "peer-next")         # 同级(兄弟)菜单后一个

    @property
    def pos(self):
        return self.value[0]

    @property
    def alias(self):
        return self.value[1]

