from django.db import connection

from rest_framework.views import APIView
from rest_framework.generics import mixins, GenericAPIView
from rest_framework.generics import ListAPIView
from rest_framework.response import Response

from .models import MenuModel, RoleGroupModel
from .serializers import MenuSerializer, RoleGroupSerializer
from constant.action import ApiActionEnum


class ListMenuApi(ListAPIView):
    serializer_class = MenuSerializer

    def get_queryset(self):
        keyword = self.request.query_params.get('keyword')
        Model = self.serializer_class.Meta.model
        fields = Model.fields()

        if keyword:
            recursive_kwargs = dict(
                key=keyword, menu_table=Model._meta.db_table,
                menu_fields=', '.join(fields),
                parent_menu_fields=', '.join(['parent.%s' % f for f in fields]),
            )

            # recursive query
            sql = """
                WITH RECURSIVE recursive_tree AS 
                (
                    SELECT {menu_fields} FROM {menu_table} 
                    WHERE (name like '%{key}%' or url like '%{key}%') and is_del=false
                    UNION 
                    SELECT {parent_menu_fields} FROM {menu_table} parent
                    INNER JOIN recursive_tree child
                    ON child.parent_id = parent.id 
                    WHERE parent.is_del=false
                )
                SELECT {menu_fields} FROM recursive_tree 
                ORDER BY parent_id, level, menu_order
            """
            cursor = connection.cursor()
            cursor.execute(sql.format(**recursive_kwargs))
            db_menu_tree_rets = cursor.fetchall()

            queryset = [Model(**dict(zip(fields, items))) for items in db_menu_tree_rets]
        else:
            queryset = Model.objects.filter(is_del=False).all()

        return queryset


class MenuTreeApi(APIView):
    def get(self, request, *args, **kwargs):
        menu_queryset = None
        include_leaf = request.query_params.get('include_leaf')
        group_id = int(request.query_params.get('group_id', 0))

        if group_id:
            role_obj = RoleGroupModel.objects.filter(id=group_id, is_del=False).first()
            menu_queryset = role_obj.get_menus()

        menu_tree = MenuModel.get_menu_tree(
            queryset=menu_queryset,
            include_leaf=include_leaf == 'true'
        )
        return Response(data=menu_tree)


class OperationsMenuApi(mixins.CreateModelMixin,
                        mixins.UpdateModelMixin,
                        GenericAPIView):
    serializer_class = MenuSerializer

    def get_object(self):
        pk = self.request.data.get('id')
        return self.serializer_class.Meta.model.objects.get(id=pk)

    def post(self, request, *args, **kwargs):
        action = request.data.pop('action', None)
        assert action in [e.action for e in ApiActionEnum.iterator()], "不合法的操作"

        if action == ApiActionEnum.DELETE.action:
            self.get_object().update_attrs(force_update=True, is_del=True)
            return Response(data=None)

        dispatch_meth = getattr(self, action)
        return dispatch_meth(request, *args, **kwargs, partial=True)


class ListRoleGroupApi(ListAPIView):
    serializer_class = RoleGroupSerializer

    def get_queryset(self):
        keyword = self.request.query_params.get('keyword')
        queryset = self.serializer_class.Meta.model.objects.all()

        if keyword:
            pass
            # queryset = queryset.filter()

        return queryset

