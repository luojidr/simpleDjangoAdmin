import os
import json
import string
import random
from importlib import reload
from urllib.parse import parse_qsl

import django
from django import template
from django.urls import reverse
from django.conf import settings
from django.utils.functional import Promise
from django.utils.html import format_html
from django.utils.encoding import force_str as force_text
from django.utils.safestring import mark_safe
from django.templatetags.static import static
from django.utils.translation import gettext_lazy as _
from django.db.models.fields.related import ForeignKey
from django.core.serializers.json import DjangoJSONEncoder
from django.contrib.admin.templatetags.admin_urls import add_preserved_filters

from permissions.models import RoleGroupModel

register = template.Library()


@register.simple_tag
def get_setting(name):
    from django.conf import settings
    return os.environ.get(name, getattr(settings, name, None))


class LazyEncoder(DjangoJSONEncoder):
    def default(self, obj):
        if isinstance(obj, Promise):
            return force_text(obj)
        return super(LazyEncoder, self).default(obj)


@register.simple_tag(takes_context=True)
def context_test(context):
    print(context)
    pass


@register.simple_tag(takes_context=True)
def home_page(context):
    """ 判断打开的是默认页还是自定义的页面 """
    home = get_setting('SIMPLE_HOME_PAGE')
    if home:
        context['home'] = home

    title = get_setting('SIMPLE_HOME_TITLE')
    icon = get_setting('SIMPLE_HOME_ICON')

    if not title:
        title = '首页'

    if not icon:
        icon = 'el-icon-menu'

    context['title'] = title
    context['icon'] = icon
    return ''


@register.filter
def get_config(key):
    return get_setting(key)


@register.filter
def get_value(value):
    return value


def format_table(d):
    html = '<table class="simple-table"><tbody>'
    for key in d:
        html += '<tr><th>{}</th><td>{}</td></tr>'.format(key, d.get(key))
    html += '</tbody></table>'
    return format_html(html)


def has_permission_in_config(config):
    """
    Recursively check if any menu or sub-menu in the configuration is configured with permissions.
    """
    if 'menus' in config:
        for menu in config['menus']:
            if has_permission_in_config(menu):
                return True
    if 'models' in config:
        for model in config['models']:
            if has_permission_in_config(model):
                return True
    if 'permission' in config:
        return True
    return


def get_filtered_menus(menus, user_permissions):
    def filter_menu(menu, permissions):
        if 'models' in menu:
            menu['models'] = [sub_menu for sub_menu in menu['models'] if 'permission' not in sub_menu or
                              sub_menu['permission'] in permissions]
            for sub_menu in menu['models']:
                filter_menu(sub_menu, permissions)
    menu_configs = [menu for menu in menus if 'permission' not in menu or menu['permission'] in user_permissions]
    for menu in menu_configs:
        filter_menu(menu, user_permissions)
    return menu_configs


@register.simple_tag(takes_context=True)
def menus(context):
    """ 控制左侧菜单栏、上侧面包屑与面包屑对应的tab页 """
    menus_data = []

    # 自定义Django应用(目前已被Vue+ElementUI定制化替代)
    app_list = context.get('app_list', [])
    for app in app_list:
        _models = [
            {
                'name': m.get('name'),
                'icon': get_icon(m.get('object_name'), m.get('name')),
                'url': m.get('admin_url'),
                'addUrl': m.get('add_url'),
                'breadcrumbs': [
                    {
                        'name': app.get('name'),
                        'icon': get_icon(app.get('app_label'), app.get('name'))
                    },
                    {
                        'name': m.get('name'),
                        'icon': get_icon(m.get('object_name'), m.get('name'))
                    }
                ]
            }
            for m in app.get('models')
        ] if app.get('models') else []

        module = {
            'name': app.get('name'),
            'icon': get_icon(app.get('app_label'), app.get('name')),
            'models': _models
        }
        menus_data.append(module)

    # 菜单栏权限控制（ MenuOwnerPermissionModel 中授予的菜单权限）
    user_id = context.request.user.id
    menus_config = RoleGroupModel.get_menu_permissions(
        user_id=user_id,
        group_id=int(context.request.COOKIES.get('cgid') or 0),  # 当前用户使用的用户组(Cookie)
    )
    group_id = menus_config.pop('group_id')
    menus_data = menus_config.get('menus')

    # 给每个菜单增加一个唯一标识，用于tab页判断
    eid = 1000
    handler_eid(menus_data, eid)
    menus_string = json.dumps(menus_data, cls=LazyEncoder)

    # 把data放入session中，其他地方可以调用
    if not isinstance(context, dict) and context.request:
        if "_menus" not in context.request.session:
            context.request.session['_menus'] = menus_string

    # 计算用户所属的角色组
    groups = RoleGroupModel.get_group_list(user_id=user_id, first_id=group_id)
    groups_string = json.dumps(groups, cls=LazyEncoder)

    return '<script type="text/javascript">' \
           'var menus={menus};' \
           'var userGroups={groups};' \
           'var currentGroupId={group_id};' \
           '</script>'.format(menus=menus_string, groups=groups_string, group_id=group_id)


def handler_eid(data, eid):
    for i in data:
        eid += 1
        i['eid'] = eid
        if 'models' in i:
            eid = handler_eid(i.get('models'), eid)
    return eid


def get_icon(obj, name=None):
    temp = get_config_icon(name)
    if temp != '':
        return temp

    _dict = {
        'auth': 'fas fa-shield-alt',
        'User': 'far fa-user',
        'Group': 'fas fa-users-cog'
    }

    temp = _dict.get(obj)
    if not temp:
        return 'far fa-circle'

    return temp


def get_config_icon(name):
    _config_icon = get_setting('SIMPLE_ICON')
    if _config_icon is None:
        return ''

    if name in _config_icon:
        return _config_icon.get(name)
    return ''


@register.simple_tag(takes_context=True)
def load_message(context):
    messages = context.get('messages')
    array = [dict(msg=msg.message, tag=msg.tags) for msg in messages] if messages else []

    return '<script id="out_message" type="text/javascript">var messages={}</script>'.format(
        json.dumps(array, cls=LazyEncoder))


@register.simple_tag(takes_context=True)
def context_to_json(context):
    json_str = '{}'

    return mark_safe(json_str)


@register.simple_tag()
def get_language():
    from django.conf import settings
    return settings.LANGUAGE_CODE.lower()


@register.filter
def get_language_code(val):
    from django.conf import settings
    return settings.LANGUAGE_CODE.lower()


@register.simple_tag(takes_context=True)
def custom_button(context):
    admin = context.get('cl').model_admin
    data = {}
    actions = admin.get_actions(context.request)
    # if hasattr(admin, 'actions'):
    # actions = admin.actions
    # 输出自定义按钮的属性

    if actions:
        i = 0
        for name in actions:
            values = {}
            fun = actions.get(name)[0]
            for key, v in fun.__dict__.items():
                if key != '__len__' and key != '__wrapped__':
                    values[key] = v
            values['eid'] = i
            i += 1
            data[name] = values

    return json.dumps(data, cls=LazyEncoder)


def get_model_fields(model, base=None):
    field_list = []
    fields = model._meta.fields
    for f in fields:
        label = f.name
        if hasattr(f, 'verbose_name'):
            label = getattr(f, 'verbose_name')

        if isinstance(label, Promise):
            label = str(label)

        if base:
            field_list.append(('{}__{}'.format(base, f.name), label))
        else:
            field_list.append((f.name, label))

    return field_list


@register.simple_tag(takes_context=True)
def search_placeholder(context):
    cl = context.get('cl')

    # 取消递归，只获取2级
    fields = get_model_fields(cl.model)

    for f in cl.model._meta.fields:
        if isinstance(f, ForeignKey):
            fields.extend(get_model_fields(f.related_model, f.name))

    verboses = []

    for s in cl.search_fields:
        for f in fields:
            if f[0] == s:
                verboses.append(f[1])
                break

    return ",".join(verboses)


def _import_reload(_modules):
    _obj = __import__(_modules, fromlist=_modules.split('.'))
    reload(_obj)
    return _obj


@register.simple_tag(takes_context=True)
def get_model_url(context):
    # reverse()
    opts = context.get("opts")
    request = context.get("request")

    key = "{}:{}_{}_changelist".format(
        get_current_app(request), opts.app_label, opts.model_name
    )
    url = reverse(key)
    preserved_filters = dict(parse_qsl(context.get("preserved_filters")))
    if "_changelist_filters" in preserved_filters:
        preserved_filters = preserved_filters["_changelist_filters"]
        url = add_preserved_filters({"preserved_filters": preserved_filters, "opts": opts}, url)
    return url


def get_current_app(request):
    app = None
    if hasattr(request, 'current_app'):
        app = getattr(request, 'current_app')
    elif hasattr(request, 'model_admin'):
        model_admin = getattr(request, 'model_admin')
        if hasattr(model_admin, 'opts'):
            opts = getattr(model_admin, 'opts')
            app = opts.app_config.name
    return app


@register.simple_tag
def has_enable_admindoc():
    from django.conf import settings
    apps = settings.INSTALLED_APPS
    return 'django.contrib.admindocs' in apps


@register.simple_tag(takes_context=True)
def has_admindoc_page(context):
    if hasattr(context, 'template_name'):
        return context.template_name.find('admin_doc') == 0
    return False


@register.simple_tag
def get_boolean_choices():
    return (
        ('True', _('Yes')),
        ('False', _('No'))
    )


@register.simple_tag(takes_context=True)
def get_previous_url(context):
    referer = context.request.META.get("HTTP_REFERER")
    if not referer or context.request.META.get("PATH_INFO") in referer:
        # return to model list
        return get_model_url(context)
    return context.request.META.get("HTTP_REFERER")


@register.simple_tag(takes_context=True)
def get_verbose_name_plural(context):
    return context['cl'].model._meta.verbose_name_plural


@register.simple_tag
def django_version_is_gte_32x():
    arrays = django.get_version().split(".")
    version = []
    for s in arrays:
        version.append(int(s))
    return tuple(version) >= (3, 2)


def get_variable_name(k=10):
    first = random.choice(string.ascii_lowercase)
    random_str = ''.join(random.choices(string.ascii_lowercase + string.digits, k=k - 1))
    return first + random_str


@register.simple_tag(takes_context=True)
def reload_javascript(context, script_dirs=None):
    """ reload `api, components, utils, views` scripts """
    scripts = []
    exclude_files = ['login.js']
    script_dirs = [d.strip() for d in (script_dirs or '').split(',') if d.strip()]

    for static_dir in settings.STATICFILES_DIRS:
        for root, dirs, files in os.walk(static_dir, topdown=False):
            static_path = root[len(static_dir) + 1:]

            try:
                entry, pathname = static_path.split(os.sep, 2)[:2]
            except ValueError:
                continue

            if entry == 'src' and pathname in script_dirs:
                for filename in files:
                    if filename in exclude_files:
                        continue

                    static_src = os.path.join('/', static_path, filename).replace(os.sep, '/')
                    scripts.append(f'<script type="text/javascript" src="{static(static_src)}"></script>')

    return "\n".join(scripts)

