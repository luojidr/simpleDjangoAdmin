# Generated by Django 4.2.7 on 2023-11-24 17:42

import core.db.base
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="GroupOwnedMenuModel",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "creator",
                    models.CharField(
                        default=core.db.base.AutoExecutor(),
                        max_length=200,
                        verbose_name="创建人",
                    ),
                ),
                (
                    "modifier",
                    models.CharField(
                        default=core.db.base.AutoExecutor(),
                        max_length=200,
                        verbose_name="创建人",
                    ),
                ),
                (
                    "create_time",
                    models.DateTimeField(auto_now_add=True, verbose_name="创建时间"),
                ),
                (
                    "update_time",
                    models.DateTimeField(auto_now=True, verbose_name="更新时间"),
                ),
                ("is_del", models.BooleanField(default=False, verbose_name="是否删除")),
                (
                    "reason",
                    models.CharField(
                        blank=True, default="", max_length=200, verbose_name="Reason"
                    ),
                ),
            ],
            options={
                "db_table": "x_permission_group_owned_menu",
            },
        ),
        migrations.CreateModel(
            name="GroupOwnedUserModel",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "creator",
                    models.CharField(
                        default=core.db.base.AutoExecutor(),
                        max_length=200,
                        verbose_name="创建人",
                    ),
                ),
                (
                    "modifier",
                    models.CharField(
                        default=core.db.base.AutoExecutor(),
                        max_length=200,
                        verbose_name="创建人",
                    ),
                ),
                (
                    "create_time",
                    models.DateTimeField(auto_now_add=True, verbose_name="创建时间"),
                ),
                (
                    "update_time",
                    models.DateTimeField(auto_now=True, verbose_name="更新时间"),
                ),
                ("is_del", models.BooleanField(default=False, verbose_name="是否删除")),
            ],
            options={
                "db_table": "x_permission_group_owned_user",
            },
        ),
        migrations.CreateModel(
            name="MenuModel",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "creator",
                    models.CharField(
                        default=core.db.base.AutoExecutor(),
                        max_length=200,
                        verbose_name="创建人",
                    ),
                ),
                (
                    "modifier",
                    models.CharField(
                        default=core.db.base.AutoExecutor(),
                        max_length=200,
                        verbose_name="创建人",
                    ),
                ),
                (
                    "create_time",
                    models.DateTimeField(auto_now_add=True, verbose_name="创建时间"),
                ),
                (
                    "update_time",
                    models.DateTimeField(auto_now=True, verbose_name="更新时间"),
                ),
                ("is_del", models.BooleanField(default=False, verbose_name="是否删除")),
                (
                    "name",
                    models.CharField(
                        blank=True, default="", max_length=200, verbose_name="Name"
                    ),
                ),
                (
                    "icon",
                    models.CharField(
                        blank=True, default="", max_length=200, verbose_name="Icon"
                    ),
                ),
                (
                    "app",
                    models.CharField(
                        blank=True,
                        default="",
                        max_length=200,
                        verbose_name="Belong to App",
                    ),
                ),
                (
                    "url",
                    models.CharField(
                        blank=True, default="", max_length=500, verbose_name="Url"
                    ),
                ),
                (
                    "component_name",
                    models.CharField(
                        blank=True,
                        default="",
                        max_length=200,
                        verbose_name="Component Name",
                    ),
                ),
                (
                    "parent_id",
                    models.IntegerField(
                        blank=True, default=0, verbose_name="Parent Menu ID"
                    ),
                ),
                (
                    "menu_order",
                    models.IntegerField(blank=True, default=1, verbose_name="Order"),
                ),
                (
                    "level",
                    models.SmallIntegerField(
                        blank=True,
                        choices=[(0, "根"), (1, "一级菜单"), (2, "二级菜单"), (3, "三级菜单")],
                        default=1,
                        verbose_name="Level",
                    ),
                ),
                (
                    "is_hidden",
                    models.BooleanField(
                        blank=True, default=False, verbose_name="Hidden"
                    ),
                ),
                (
                    "remark",
                    models.CharField(
                        blank=True, default="", max_length=200, verbose_name="Remark"
                    ),
                ),
            ],
            options={
                "db_table": "x_permission_menu",
                "ordering": ("parent_id", "level", "menu_order"),
            },
        ),
        migrations.CreateModel(
            name="RoleGroupModel",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "creator",
                    models.CharField(
                        default=core.db.base.AutoExecutor(),
                        max_length=200,
                        verbose_name="创建人",
                    ),
                ),
                (
                    "modifier",
                    models.CharField(
                        default=core.db.base.AutoExecutor(),
                        max_length=200,
                        verbose_name="创建人",
                    ),
                ),
                (
                    "create_time",
                    models.DateTimeField(auto_now_add=True, verbose_name="创建时间"),
                ),
                (
                    "update_time",
                    models.DateTimeField(auto_now=True, verbose_name="更新时间"),
                ),
                ("is_del", models.BooleanField(default=False, verbose_name="是否删除")),
                (
                    "name",
                    models.CharField(
                        blank=True, default="", max_length=200, verbose_name="Name"
                    ),
                ),
                (
                    "desc",
                    models.CharField(
                        blank=True, default="", max_length=500, verbose_name="Desc"
                    ),
                ),
                (
                    "menus",
                    models.ManyToManyField(
                        related_name="roles",
                        through="permissions.GroupOwnedMenuModel",
                        to="permissions.menumodel",
                    ),
                ),
                (
                    "users",
                    models.ManyToManyField(
                        related_name="roles",
                        through="permissions.GroupOwnedUserModel",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "db_table": "x_permission_group",
                "ordering": ("id",),
            },
        ),
        migrations.AddField(
            model_name="groupownedusermodel",
            name="group",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to="permissions.rolegroupmodel",
            ),
        ),
        migrations.AddField(
            model_name="groupownedusermodel",
            name="user",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AddField(
            model_name="groupownedmenumodel",
            name="group",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to="permissions.rolegroupmodel",
            ),
        ),
        migrations.AddField(
            model_name="groupownedmenumodel",
            name="menu",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to="permissions.menumodel",
            ),
        ),
    ]
