from django.db import connection
from django.db.models import Q
from django.utils.functional import cached_property
from rest_framework import serializers

from .models import RoleGroupModel, MenuModel
from users.serializers import SimpleUsersSerializer


class MenuSerializer(serializers.ModelSerializer):
    # level: 展示名字，而不是数字
    level = serializers.CharField(source='get_level_display', read_only=True, max_length=100, help_text="层级")
    parent_paths = serializers.SerializerMethodField()
    group_id = serializers.SerializerMethodField()
    group_name = serializers.SerializerMethodField()

    class Meta:
        model = MenuModel
        fields = model.fields() + ['parent_paths', 'group_id', 'group_name']

    @cached_property
    def root_menu_tree(self):
        return self.Meta.model.get_menu_tree()

    @cached_property
    def menu_parent_paths(self):
        # 计算菜单的父路径
        menu_parent_dict = {}
        stack = [self.root_menu_tree]

        while stack:
            menu = stack.pop(0)
            menu_parent_dict[menu['id']] = ' / '.join(menu['parent_paths'])
            stack.extend(menu.get('children') or [])

        return menu_parent_dict

    def get_parent_paths(self, obj):
        return self.menu_parent_paths.get(obj.id, '')

    @cached_property
    def role_groups(self):
        objects = self.instance or []
        menu_ids = [menu_obj.id for menu_obj in (objects if isinstance(objects, list) else [objects])]

        fields = ['menus', 'name', 'id']
        query = dict(menus__in=menu_ids, is_del=False)
        group_queryset = RoleGroupModel.objects.filter(**query).prefetch_related('menus').values(*fields)

        return {g.pop('menus'): g for g in group_queryset}

    def get_group_name(self, obj):
        return self.role_groups.get(obj.id, {}).get('name')

    def get_group_id(self, obj):
        return self.role_groups.get(obj.id, {}).get('id')

    def _get_levels(self, menu_id):
        sql = """
            WITH RECURSIVE recursive_tree AS 
                (
                    SELECT id, NAME, parent_id FROM {tb}
                    WHERE id={menu_id} AND is_del=False
                    UNION 
                    SELECT parent.id, parent.NAME, parent.parent_id FROM {tb} parent
                    INNER JOIN recursive_tree child
                    ON child.parent_id = parent.id 
                    WHERE parent.is_del=false
                )
             SELECT COUNT(*) FROM recursive_tree WHERE id<>{menu_id}
        """
        cursor = connection.cursor()
        cursor.execute(sql.format(tb=self.Meta.model._meta.db_table, menu_id=menu_id))
        db_ret = cursor.fetchone()

        return db_ret and db_ret[0] or 0

    def renew_menu_position_and_group(self, instance):
        """ 调整同级菜单位置顺序和renew """
        Model = self.Meta.model
        menu_position = self.initial_data.get('menu_position')

        if not menu_position:
            instance.delete()
            raise ValueError('菜单<name:%s>位置未设置' % instance.name)

        if menu_position['parent_id'] != instance.parent_id:
            instance.delete()
            raise ValueError('菜单<name:%s>不属于同一个父菜单' % instance.name)

        instance.level = self._get_levels(menu_id=instance.id)
        instance.save()

        menu_children = menu_position['children']
        objects = list(Model.objects.filter(parent_id=instance.parent_id).all())
        db_menu_children_dict = {obj.uniq_key: obj for obj in objects}

        for i, menu_child in enumerate(menu_children):
            menu_obj = db_menu_children_dict.pop(menu_child['uniq_key'], None)

            if menu_obj is not None:
                menu_obj.menu_order = i + 1
                menu_obj.is_del = False
                menu_obj.save()

        # 添加/修改所属角色组
        group_id = self.initial_data.get('group_id', 0)
        role_group = RoleGroupModel.objects.filter(id=group_id, is_del=False).first()
        role_group and role_group.menus.add(instance)

        delete_ids = [o.id for o in db_menu_children_dict.values()]
        Model.objects.filter(id__in=delete_ids).update(is_del=True)

    def create(self, validated_data):
        instance = super().create(validated_data)
        instance.update_attrs(force_update=True, is_del=True)
        self.renew_menu_position_and_group(instance)

        return instance

    def update(self, instance, validated_data):
        instance = super().update(instance, validated_data)
        self.renew_menu_position_and_group(instance)

        return instance


class RoleGroupSerializer(serializers.ModelSerializer):
    # queryset = MenuModel.objects.filter(is_del=False).all()  # 多对多 queryset 忽略

    # menus = serializers.StringRelatedField(many=True, read_only=True, allow_null=True)  # 多对多单个字段
    # menu_users = serializers.StringRelatedField(many=True, read_only=True, allow_null=True)  # 多对多单个字段

    # menus = MenuSerializer(many=True, read_only=True)           # 角色组拥有的所有菜单(同上)
    # users = SimpleUsersSerializer(many=True, read_only=True)    # 角色组拥有的所有人员(同上)

    menutree = serializers.SerializerMethodField()

    class Meta:
        model = RoleGroupModel
        fields = model.fields() + ['menus', 'users', 'menutree']

    def get_menutree(self, obj):
        return obj.get_menu_tree_of_group()

    def _update_permissions(self, instance):
        user_ids = self.initial_data.get('user_ids') or []
        menu_ids = self.initial_data.get('menu_ids') or []

        # 更新用户权限/菜单权限
        instance.update_users_or_menus(user_ids=user_ids, menu_ids=menu_ids)

    def create(self, validated_data):
        instance = super().create(validated_data)

        self._update_permissions(instance)
        return instance

    def update(self, instance, validated_data):
        instance = super().update(instance, validated_data)

        self._update_permissions(instance)
        return instance

