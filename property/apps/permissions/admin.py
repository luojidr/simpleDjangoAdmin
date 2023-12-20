from django.contrib import admin

from auditlog.registry import auditlog

from .models import MenuModel

admin.site.register(MenuModel)
auditlog.register(MenuModel)
