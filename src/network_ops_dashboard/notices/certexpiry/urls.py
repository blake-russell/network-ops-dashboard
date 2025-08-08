"""certexpiry URL Configuration

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
    re_path(r'^$', views.certexpiry, name='certexpiry'),
    re_path(r'^update/$', views.certexpiry_update, name='certexpiry_update'),
    re_path(r'^archive/(?P<pk>[0-9]{1,10})/$', views.certexpiry_archive, name='certexpiry_archive'),
    re_path(r'^provider/$', views.certexpiry_provider, name='certexpiry_provider'),
    re_path(r'^provider/add/$', views.certexpiry_provider_add, name='certexpiry_provider_add'),
    re_path(r'^provider/edit/(?P<pk>[0-9]{1,10})/$', views.certexpiry_provider_edit, name='certexpiry_provider_edit'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT) + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)