"""dj_backend URL Configuration

The `urlpatterns` list routes URLs to controller. For more information please see:
    https://docs.djangoproject.com/en/3.0/topics/http/urls/
Examples:
Function controller
    1. Add an import:  from my_app import controller
    2. Add a URL to urlpatterns:  path('', controller.home, name='home')
Class-based controller
    1. Add an import:  from other_app.controller import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.apps import apps
from django.contrib import admin
from django.conf import settings
from django.urls import path, include, re_path

urlpatterns = [
    path("admin/", admin.site.urls),
]

urlpatterns += [
    path(r"", include('%s.urls' % app.name))
    for app in apps.app_configs.values()
    if app.path.startswith(str(settings.APPS_DIR))
]
