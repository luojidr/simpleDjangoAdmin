from django.urls import re_path, path

from . import views

urlpatterns = [
    # Template
    re_path("^$", view=views.IndexView.as_view(), name="index"),
    path("logout/", view=views.LogoutView.as_view(), name="logout"),
    path("user/login/", view=views.LoginView.as_view(), name="login"),
    re_path("^api/user/change_password$", view=views.ChangePasswordApi.as_view(), name="change_password_api"),

    # Api
    re_path("^api/user/search$", view=views.SearchUserApi.as_view(), name="search_user_api"),

]

