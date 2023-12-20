from django.urls import re_path

from . import views


urlpatterns = [
    re_path(
        "^api/generics/template/(?P<template_name>.*?)$",
        view=views.GenericTemplateAPI.as_view(),
        name="generics_template_api"
    ),

    re_path(
        "^api/generics/app/options$",
        view=views.GenericAppOptionsApi.as_view(),
        name="generics_app_options_api"
    ),

    re_path(
        "^api/generics/model/options$",
        view=views.GenericModelOptionsApi.as_view(),
        name="generics_model_options_api"
    ),

    re_path(
        "^api/generics/model/choice$",
        view=views.GenericModelChoiceApi.as_view(),
        name="generics_model_choice_api"
    ),

    re_path(
        "^api/generics/default/form$",
        view=views.GenericDefaultFormAPI.as_view(),
        name='generics_default_form_api'
    ),

    re_path(
        "^api/generics/search$",
        view=views.ListGenericSearchAPI.as_view(),
        name="generics_search_api"
    ),

    re_path(
        "^api/generics/operations/do$",
        view=views.GenericDoOperationsAPI.as_view(),
        name="generics_operations_do_api"
    ),
]

