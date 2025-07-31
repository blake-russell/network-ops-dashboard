"""f5lb URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls import url, include
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    url(r'^vipcertrenew/$', views.f5lb_vipcertrenew, name='f5lb_vipcertrenew'),
    url(r'^vipcertrenew/add/$', views.f5lb_vipcertrenew_add, name='f5lb_vipcertrenew_add'),
    url(r'^vipcertrenew/edit/(?P<pk>[0-9]{1,10})/$', views.f5lb_vipcertrenew_edit, name='f5lb_vipcertrenew_edit'),
    url(r'^vipcertrenew/archive/(?P<pk>[0-9]{1,10})/$', views.f5lb_vipcertrenew_archive, name='f5lb_vipcertrenew_archive'),
    url(r'^vipcertrenew/run/(?P<pk>[0-9]{1,10})/$', views.f5lb_vipcertrenew_run, name='f5lb_vipcertrenew_run'),
    url(r'^loadconfigoptions/(?P<device_id>[0-9]{1,10})/$', views.f5lb_loadconfigoptions, name='f5lb_loadconfigoptions'),
    path('get_config_options/<int:device_id>/', views.f5lb_get_config_options, name='f5lb_get_config_options'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT) + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)