"""dtss URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.9/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf import settings
from django.conf.urls import include, url
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, re_path
from django.contrib import admin

from constants import URL_APPEND

admin.autodiscover()
admin.site.enable_nav_sidebar = False


urlpatterns = [
    url(r'^' + URL_APPEND + 'admin/', admin.site.urls),
    url(r'^' + URL_APPEND + 'auth/', include(('authentication.urls', 'authentication'), namespace='authentication')),
    url(r'^' + URL_APPEND + 'web_auth/', include(('web_auth.urls', 'web_auth'), namespace='web_auth')),
    url(r'^' + URL_APPEND + 'management/', include(('management.urls', 'management'), namespace='management')),
    url(r'^' + URL_APPEND + 'registercall/', include(('registercall.urls', 'registercall'), namespace='register_call')),
    url(r'^' + URL_APPEND + 'taskmanager/', include(('task_manager.urls', 'task_manager'), namespace='task_manager')),
    url(r'^' + URL_APPEND + 'registerhelper/',
        include(('register_helper.urls', 'register_helper'), namespace='register_helper')),
    url(r'^' + URL_APPEND + 'ivr/', include(('ivr.urls', 'ivr'), namespace='ivr')),
    url(r'^' + URL_APPEND + 'kem/',
        include(('wwh_form_delivery.urls', 'wwh_form_delivery'), namespace='wwh_form_delivery')),
    url(r'^' + URL_APPEND, include(('dashboard.urls', 'dashboard'), namespace='dashboard')),
    re_path(r'^' + URL_APPEND, include('notes.urls')),
]

urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
