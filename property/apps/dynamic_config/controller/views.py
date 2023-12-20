from datetime import datetime

from django.urls import reverse
from django.conf import settings
from django.shortcuts import render
from django.views.generic import TemplateView, View
from django.http import HttpResponseRedirect
from django.contrib.auth import authenticate, logout, get_user_model
