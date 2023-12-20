from django.urls import re_path

from . import views


urlpatterns = [
    re_path("^api/permissions/menu/list$", view=views.ListMenuApi.as_view(), name="permissions_menu_list_api"),
    re_path("^api/permissions/menu/tree$", view=views.MenuTreeApi.as_view(), name="permissions_menu_tree_api"),
    re_path(
        "^api/permissions/menu/operations$",
        view=views.OperationsMenuApi.as_view(),
        name="permissions_menu_operations_api"
    ),

    re_path(
        "^api/permissions/rolegroup/list$",
        view=views.ListRoleGroupApi.as_view(),
        name="permissions_rolegroup_list_api"
    ),
]
