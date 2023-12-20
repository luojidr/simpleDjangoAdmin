from rest_framework import serializers

from .models import UsersModel


class SimpleUsersSerializer(serializers.ModelSerializer):
    class Meta:
        model = UsersModel
        fields = ['id', 'avatar', 'name_chz', 'name_eng', 'username', 'department', 'position']

