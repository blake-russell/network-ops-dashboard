"""oncall URL Configuration

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

from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls import url, include
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    url(r'^$', views.oncall, name='oncall'),
    path('update/<int:pk>/', views.oncall_update_incident_log, name='oncall_update_incident_log'),
    path('incident/close/<int:incident_id>/', views.oncall_close_incident, name='oncall_close_incident'),
    path('incident/open/<int:incident_id>/', views.oncall_open_incident, name='oncall_open_incident'),
    path('incident/add/', views.oncall_add_incident, name='oncall_add_incident'),
    path('incident/log/', views.oncall_incident_log, name='oncall_incident_log'),
    path('incident/print/', views.oncall_incident_print, name='oncall_incident_print'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT) + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)