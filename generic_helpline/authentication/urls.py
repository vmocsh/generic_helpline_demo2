"""
Url config file for Register Helper App
"""
from django.conf.urls import url

from .views import Login, Logout, ResetPassword, GenerateResetPassword

urlpatterns = [
    url(r'^login/$', Login.as_view(), name='login'),
    url(r'^logout/$', Logout.as_view(), name='logout'),
    url(r'^generate_reset_password/$', GenerateResetPassword.as_view(), name='generateresetpassword'),
    url(r'^reset_password/(?P<id>.+)/$', ResetPassword.as_view(), name='resetpassword'),
]
