from django.conf import settings
from django.urls import re_path, path
from . import views

# 为了符合swagger的展示方便，强烈建议在同一app内使用相同前缀
api_urlpatterns = [
    path("t_test", view=views.TestConstanceConfigApi.as_view(), name="constance_config_test"),
    path("edit", view=views.UpdateConstanceConfigApi.as_view(), name="constance_config_edit"),

]

view_urlpatterns = [
    path("list", view=views.ListDynamicConfigView.as_view(), name="dynamic_config_list"),
]

