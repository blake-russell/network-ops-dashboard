"""inventory URL Configuration

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
    re_path(r'^$', views.inventory_home, name='inventory_home'),
    re_path(r'^add/$', views.inventory_add, name='inventory_add'),
    re_path(r'^edit/(?P<pk>[0-9]{1,10})/$', views.inventory_edit, name='inventory_edit'),
    re_path(r'^platform/$', views.platform_home, name='platform_home'),
    re_path(r'^platform/add/$', views.platform_add, name='platform_add'),
    re_path(r'^platform/edit/(?P<pk>[0-9]{1,10})/$', views.platform_edit, name='platform_edit'),
    re_path(r'^site/$', views.site_home, name='site_home'),
    re_path(r'^site/add/$', views.site_add, name='site_add'),
    re_path(r'^site/edit/(?P<pk>[0-9]{1,10})/$', views.site_edit, name='site_edit'),
    re_path(r'^devicetag/$', views.devicetag_home, name='devicetag_home'),
    re_path(r'^devicetag/add/$', views.devicetag_add, name='devicetag_add'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT) + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)