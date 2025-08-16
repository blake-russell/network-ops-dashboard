"""sitesettings URL Configuration

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
from django.urls import re_path
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views
from network_ops_dashboard.sitesettings import views

urlpatterns = [
    re_path(r'^edit/$', views.sitesettings_edit, name='sitesettings_edit'),
    re_path(r'^websites/$', views.websites_home, name='websites_home'),
    re_path(r'^websites/add/$', views.websites_add, name='websites_add'),
    re_path(r'^websites/edit/(?P<pk>[0-9]{1,10})/$', views.websites_edit, name='websites_edit'),
    re_path(r'^secrets/$', views.secrets_home, name='secrets_home'),
    re_path(r'^secrets/add/$', views.secrets_add, name='secrets_add'),
    re_path(r'^secrets/edit/(?P<pk>[0-9]{1,10})/$', views.secrets_edit, name='secrets_edit'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT) + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)