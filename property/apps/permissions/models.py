import re
import random
import string
import logging
import os.path
from collections import deque
from typing import List, Union

from django.db import models
from django.conf import settings
from django.core import validators
from django.contrib.auth import get_user_model

from core.db.base import BaseModelMixin

UserModel = get_user_model()


class MenuModel(BaseModelMixin):
    """ 菜单 """
    MENU_LEVEL_CHOICES = [
        (0, '根'),
        (1, '一级菜单'),
        (2, '二级菜单'),
        (3, '三级菜单'),
    ]

    name = models.CharField('Name', max_length=200, default='', null=True, blank=True)
    icon = models.CharField('Icon', max_length=200, default='', null=True, blank=True)
    app = models.CharField('Belong to App', max_length=200, default='', null=True, blank=True)
    url = models.CharField('Url', max_length=500, default='', null=True, blank=True)
    model = models.CharField('Model', max_length=200, default='', null=True, blank=True)
    component_name = models.CharField('Component Name', max_length=200, default='', null=True, blank=True)
    form_component_name = models.CharField('Form Component Name', max_length=200, default='', null=True, blank=True)
    parent_id = models.IntegerField('Parent Menu ID', default=0, null=True, blank=True)
    menu_order = models.IntegerField('Order', default=1, null=True, blank=True)
    level = models.SmallIntegerField('Level', choices=MENU_LEVEL_CHOICES, default=1, null=True, blank=True)
    is_form = models.BooleanField('Form', default=False, null=True, blank=True)
    is_hidden = models.BooleanField('Hidden', default=False, null=True, blank=True)
    uniq_key = models.CharField('UUID',
                                validators=[validators.MinLengthValidator(6)],
                                unique=True, max_length=6, null=True, blank=True
                                )
    remark = models.CharField('Remark', max_length=200, default='', null=True, blank=True)

    class Meta:
        db_table = 'x_permission_menu'
        ordering = ('parent_id', 'level', 'menu_order')

    def __str__(self):
        return self.name

    @classmethod
    def get_uniq_key(cls):
        return ''.join([random.choice(string.ascii_letters) for i in range(6)])

    def get_component_path(self, component_name=None):
        """ 获取组件路径， 默认匹配 self.component_name 路径 """
        component_name = (component_name or self.component_name or "").strip()
        regex = re.compile(r"""Vue\.component\(['"](.*?)['"],\s*?\{""", re.S | re.M)

        if not component_name:
            return ''

        if settings.DEBUG:
            static_dir = settings.STATICFILES_DIRS[0]
        else:
            static_dir = settings.STATIC_ROOT
        static_dir = os.path.join(static_dir, 'src')

        for root, dirs, files in os.walk(os.path.join(static_dir, 'views'), topdown=False):
            for filename in files:
                with open(os.path.join(root, filename), encoding='utf-8') as fp:
                    text = fp.read()
                    match = regex.search(text)

                    if match is not None and match.group(1) == component_name:
                        component_path = os.path.join(root[len(static_dir) + 1:], filename)
                        return '../' + component_path.replace(os.sep, '/')

        logging.error('组件<%s:%s>文件不存在', self.name, component_name)
        return ''

    @classmethod
    def get_menu_root_id(cls):
        root = cls.objects.get(name='根', is_del=False)
        return root.id

    @classmethod
    def get_menu_tree(cls, queryset=None, include_leaf: bool = True):
        """ 菜单树
        :param queryset: 可选，用户组的菜单集
        :param include_leaf: bool, 是否包含叶子菜单
        :return:
        """
        menu_tree = {}
        fields = cls.fields(exclude=['menu_order', 'level', 'remark', 'is_del'])

        if queryset is None:
            queryset = cls.objects.filter(is_del=False).all()

        for menu in queryset:
            menu_item = {attr: getattr(menu, attr) for attr in fields}

            menu_id = menu_item['id']
            parent_id = menu_item['parent_id']
            menu_item.update(value=menu_id, label=menu_item.pop('name'), is_leaf=True)
            parent_paths = menu_item.setdefault('parent_paths', [])  # 当前菜单的父菜单路径

            menu_tree[menu_id] = menu_item  # 更新menu_item

            if parent_id in menu_tree:
                parent_menu = menu_tree[parent_id]
                parent_menu['is_leaf'] = False
                parent_menu.setdefault('children', []).append(menu_item)

                # 更新当前菜单的父菜单路径
                p_menu_parent_path = parent_menu['parent_paths']  # 父菜单的父菜单路径
                parent_paths.extend(p_menu_parent_path + [parent_menu['label']])

        menu_tree = menu_tree.get(cls.get_menu_root_id(), {})

        # 判断是否包含叶子菜单
        if not include_leaf:
            q = deque([menu_tree])

            while q:
                item = q.popleft()
                new_children = [child for child in item.pop('children', []) if not child['is_leaf']]
                new_children and item.update(children=new_children)
                q.extend(new_children)

        return menu_tree


class RoleGroupModel(BaseModelMixin):
    """ 角色组 """
    name = models.CharField('Name', max_length=200, default='', null=True, blank=True)
    desc = models.CharField('Desc', max_length=500, default='', null=True,  blank=True)

    # many_to_many: menu, group; related_name: 反向查询
    # through_fields: 第一个字段必须是本模型的
    menus = models.ManyToManyField(
        MenuModel,
        through='GroupOwnedMenuModel',
        through_fields=['group', 'menu'],
        related_name='roles',
    )

    # many_to_many: user, group; related_name: 反向查询
    users = models.ManyToManyField(
        UserModel,
        through='GroupOwnedUserModel',
        through_fields=['group', 'user'],
        related_name='roles',
    )

    class Meta:
        db_table = 'x_permission_group'
        ordering = ('-id', )

    def get_menus(self, ordering=()):
        menu_queryset = self.menus.filter(is_del=False).all()

        if ordering:
            menu_queryset = menu_queryset.order_by(*ordering).all()

        return menu_queryset

    def get_users(self):
        user_queryset = self.users.filter(is_del=False).all()
        return user_queryset

    def get_menu_tree_of_group(self):
        return MenuModel.get_menu_tree(queryset=self.get_menus())

    @classmethod
    def get_group_list(cls, user_id: int, first_id: Union[int, None] = None) -> List[dict]:
        """ 获取用户所有的用户组权限 """
        group_list = []
        user = UserModel.objects.get(id=user_id or 0, is_del=False)
        queryset = user.roles.filter(is_del=False).all()

        for obj in queryset:
            group_id = obj.id
            item = dict(id=group_id, name=obj.name)

            if group_id == first_id:
                group_list.insert(0, item)
            else:
                group_list.append(item)

        return group_list

    @classmethod
    def get_menu_permissions(cls, user_id: int, group_id: Union[int, None] = None):
        """ 反向查询: 获取当前用户对应的角色菜单组 """
        user = UserModel.objects.get(id=user_id or 0, is_del=False)

        group_query = dict(is_del=False)
        group_id and group_query.update(id=group_id)
        group_queryset = user.roles.filter(**group_query).all()

        role_group_obj = group_queryset.first()
        exclude_fields = ['level', 'menu_order', 'remark']

        if role_group_obj:
            menu_list = [
                dict(
                    menu.to_dict(exclude=exclude_fields),
                    component_path=menu.get_component_path(),
                    form_component_path=menu.get_component_path(menu.form_component_name)
                )
                for menu in role_group_obj.get_menus()
            ]
            menu_map = {menu_item['id']: menu_item for menu_item in menu_list}

            for menu_item in menu_list:
                menu_item.pop('id')
                parent_id = menu_item.pop('parent_id')
                parent_id and menu_map[parent_id].setdefault('models', []).append(menu_item)
        else:
            group_id, menu_map = 0, {}

        root_menu_id = MenuModel.get_menu_root_id()
        menus_config = dict(
            system_keep=True, dynamic=True, group_id=group_id,
            menus=menu_map.get(root_menu_id, {}).get('models', []),
        )

        return menus_config

    def update_users_or_menus(self, user_ids: Union[List[int], None] = None, menu_ids: Union[List[int], None] = None):
        """ 更新用户或菜单 """
        permissions = [
            dict(m2m_field=self.users, require_bound_ids=user_ids or []),
            dict(m2m_field=self.menus, require_bound_ids=menu_ids or []),
        ]

        for item in permissions:
            m2m_field = item['m2m_field']
            require_bound_ids = item['require_bound_ids']

            queryset = m2m_field.filter(is_del=False).all()
            db_bound_ids = [obj.id for obj in queryset]

            # 新增需要绑定的用户/菜单
            add_bound_ids = list(set(require_bound_ids) - set(db_bound_ids))
            m2m_field.add(*add_bound_ids)

            # 用户设置为管理员
            if m2m_field.target_field_name == 'user':
                queryset.update(is_active=True, is_staff=True, is_superuser=True)

            # 删除未绑定的用户/菜单
            remove_bound_ids = list(set(db_bound_ids) - set(require_bound_ids))
            m2m_field.remove(*remove_bound_ids)


class GroupOwnedMenuModel(BaseModelMixin):
    """ 角色组拥有的菜单 """
    group = models.ForeignKey(to=RoleGroupModel, null=True, on_delete=models.SET_NULL)
    menu = models.ForeignKey(to=MenuModel, null=True, on_delete=models.SET_NULL)
    reason = models.CharField('Reason', max_length=200, default='', blank=True)

    class Meta:
        db_table = 'x_permission_group_owned_menu'


class GroupOwnedUserModel(BaseModelMixin):
    """ 角色组拥有的用户 """
    group = models.ForeignKey(RoleGroupModel, null=True, on_delete=models.SET_NULL)
    user = models.ForeignKey(UserModel, null=True, on_delete=models.SET_NULL)

    class Meta:
        db_table = 'x_permission_group_owned_user'
