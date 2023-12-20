import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.dev")
django.setup()

from property.apps.storage.models import AccountModel
from property.apps.users.models import UsersModel

from guardian.shortcuts import assign_perm

user_obj = UsersModel.objects.get(id=3)
account_obj = AccountModel.objects.get(id=14)

perm = user_obj.has_perm("storage.add_accountmodel", account_obj)
print("perm:", perm)

if not perm:
    assign_perm("storage.add_accountmodel", user_obj, account_obj)

