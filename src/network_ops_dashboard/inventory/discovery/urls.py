"""inventory/discovery URL Configuration

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
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    re_path(r'^start/$', views.inventory_discovery_start, name='inventory_discovery_start'),
    re_path(r'^results/(?P<job_id>[0-9a-f-]{36})/$', views.inventory_discovery_results, name='inventory_discovery_results'),
    re_path(r'^status/(?P<job_id>[0-9a-f-]{36})/$', views.inventory_discovery_status, name='inventory_discovery_status'),
    re_path(r'^install/<(?P<device_id>[0-9]{1,10})/$', views.inventory_discovery_install, name='inventory_discovery_install'),
]