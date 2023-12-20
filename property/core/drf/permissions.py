from rest_framework import permissions
from rest_framework import exceptions

from rest_framework import authentication
from rest_framework_jwt import authentication


class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    自定义权限只允许对象的所有者编辑它。
    """

    def has_permission(self, request, view):
        """ request 基本权限校验 """
        token = request.query_params.get("token")

        # if token is None:
        #     token = request.data.get("token")
        #
        # if token is None:
        #     raise exceptions.PermissionDenied("你没有权限访问此接口")

        return bool(request.user and request.user.is_authenticated and request.is_agree)

    def has_object_permission(self, request, view, obj):
        # 读取权限允许任何请求，
        # 所以我们总是允许GET，HEAD或OPTIONS请求。
        if request.method in permissions.SAFE_METHODS:
            return True

        # 只有该snippet的所有者才允许写权限。
        return obj.owner == request.user
