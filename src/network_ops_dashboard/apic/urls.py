"""apic URL Configuration

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
    re_path(r'^createinterface/$', views.apic_createinterface, name='apic_createinterface'),
    re_path(r'^createinterface/add/$', views.apic_createinterface_add, name='apic_createinterface_add'),
    re_path(r'^createinterface/edit/(?P<pk>[0-9]{1,10})/$', views.apic_createinterface_edit, name='apic_createinterface_edit'),
    re_path(r'^createinterface/archive/(?P<pk>[0-9]{1,10})/$', views.apic_createinterface_archive, name='apic_createinterface_archive'),
    re_path(r'^createinterface/run/(?P<pk>[0-9]{1,10})/$', views.apic_createinterface_run, name='apic_createinterface_run'),
    re_path(r'^createinterface/intf/$', views.apic_createinterface_intf, name='apic_createinterface_intf'),
    re_path(r'^createinterface/addintf/(?P<pk>[0-9]{1,10})/$', views.apic_createinterface_addintf, name='apic_createinterface_addintf'),
    re_path(r'^createinterface/editintf/(?P<pk>[0-9]{1,10})/$', views.apic_createinterface_editintf, name='apic_createinterface_editintf'),
    re_path(r'^createinterface/delintf/(?P<pk>[0-9]{1,10})/$', views.apic_createinterface_delintf, name='apic_createinterface_delintf'),
    re_path(r'^loadconfigoptions/(?P<device_id>[0-9]{1,10})/$', views.apic_loadconfigoptions, name='apic_loadconfigoptions'),
    path('get_config_options/<int:device_id>/', views.apic_get_config_options, name='apic_get_config_options'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT) + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)