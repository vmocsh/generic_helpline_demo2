"""
Url config file for RegisterCall App
"""
from django.conf.urls import url

from .views import RegisterCall

urlpatterns = [
    url(r'^$', RegisterCall.as_view(), name='handle_request'),
]
