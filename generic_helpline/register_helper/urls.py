"""
Url config file for Register Helper App
"""
from django.conf.urls import url

from .views import RegisterHelper

urlpatterns = [
    url(r'^$', RegisterHelper.as_view(), name='register_helper'),
]
