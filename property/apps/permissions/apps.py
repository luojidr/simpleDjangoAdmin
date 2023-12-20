from collections import deque

from django.apps import AppConfig
from django.db.utils import ProgrammingError, OperationalError


class PermissionsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "permissions"
    verbose_name = '权限'

    def ready(self):
        from .models import MenuModel, RoleGroupModel

        sys_desc = '系统载入'
        menu_model_name = MenuModel._meta.model_name
        group_model_name = RoleGroupModel._meta.model_name
        try:
            admin_role, _ = RoleGroupModel.objects.get_or_create(name='超级管理员', desc=sys_desc)
        except (ProgrammingError, OperationalError):
            pass

        menutree = dict(
            name='根', icon='', app='', url='', model='', component_name='',
            form_component_name='', level=0, remark=sys_desc,
            children=[
                dict(
                    name='权限管理', icon='el-icon-menu', app=self.name, url='', model='',
                    component_name='', form_component_name='', level=1,
                    children=[
                        dict(
                            name='角色组管理', icon='el-icon-user-solid', app=self.name,
                            url='/role-group-mgr', level=2, component_name='role-group-mgr',
                            model=group_model_name, form_component_name='role-group-form',
                        ),
                        dict(
                            name='菜单管理', icon='el-icon-menu', app=self.name,
                            url='/menu-mgr', level=2, component_name='menu-mgr',
                            model=menu_model_name, form_component_name='menu-form',
                        ),
                        dict(
                            name='菜单表单', icon='', app=self.name, url='/menu-form',
                            component_name='menu-form', model=menu_model_name,
                            form_component_name='', level=2, is_form=1, is_hidden=1,
                        )
                    ]
                ),

                dict(
                    name='提交表单', icon='', app=self.name, url='/submit-form', model='',
                    component_name='submit-form', form_component_name='',
                    level=1, is_form=1, is_hidden=1, remark='通用性提交表单组件'
                )
            ]
        )

        q = deque([(menutree, 0, 0)])
        while q:
            menu_item, parent_id, menu_order = q.popleft()
            children = menu_item.pop('children', [])

            try:
                menu_obj, is_created = MenuModel.objects.get_or_create(**menu_item)
                admin_role.menus.add(menu_obj)

                if is_created:
                    uniq_key = MenuModel.get_uniq_key()
                    attrs = dict(menu_order=menu_order,  parent_id=parent_id, uniq_key=uniq_key)
                    menu_item.get('remark') and attrs.update(remark=menu_item['remark'])
                    menu_obj.update_attrs(force_update=True, **attrs)

                for index, child in enumerate(children, 1):
                    q.append((child, menu_obj.id, index))
            except (ProgrammingError, OperationalError):
                pass
