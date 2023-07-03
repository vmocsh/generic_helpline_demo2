from django.urls import re_path, include, path
from rest_framework import routers

from . import views
from django.conf.urls import url
from django.views.generic import TemplateView
from rest_framework.authtoken import views as authviews

urlpatterns = [
    url(r'^api-token-auth/$', authviews.obtain_auth_token),
    url(r'^submit/$', views.submit_form, name='submit_form'),
    url(r'^task/(?P<task_id>\d+)/(?P<otp>\d+)$', views.load_task, name='task'),
    url(r'^form_response/$', TemplateView.as_view(template_name="form_response.html"), name='form_response'),
    url(r'^get_otp/$', views.get_otp, name='get_otp'),
    url(r'^login/$', TemplateView.as_view(template_name='login_otp.html'), name='login'),
    url(r'^generate_otp/$', views.generate_otp, name='generate_otp'),
    path('updateduserlist/', views.UpdatedUserList.as_view()),
    path('whatsappusers/', views.WhatsAppUserView.as_view()),
    url(r'^validate/$', views.validate_credentials, name='validate'),
    path('api/whatsapp_message/', views.WhatsAppMessageListView.as_view()),
    path('api/whatsapp_message/<int:pk>/', views.WhatsAppMessageDetailView.as_view())
]
