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

from django.urls import path, re_path
from django.conf import settings
from django.conf.urls.static import static
from . import views

urlpatterns = [
    re_path(r'^$', views.oncall, name='oncall'),
    re_path(r'^update/(?P<pk>[0-9]{1,10})/$', views.oncall_update_incident_log, name='oncall_update_incident_log'),
    re_path(r'^incident/close/(?P<incident_id>[0-9]{1,10})/$', views.oncall_close_incident, name='oncall_close_incident'),
    re_path(r'^incident/open/(?P<incident_id>[0-9]{1,10})/$', views.oncall_open_incident, name='oncall_open_incident'),
    re_path(r'^incident/add/$', views.oncall_add_incident, name='oncall_add_incident'),
    re_path(r'^incident/log/$', views.oncall_incident_log, name='oncall_incident_log'),
    re_path(r'^incident/print/$', views.oncall_incident_print, name='oncall_incident_print'),
    re_path(r'^incident/email/$', views.oncall_incident_email, name='oncall_incident_email'),
    re_path(r'^oncall/email/save/$', views.oncall_email_save_settings, name='oncall_email_save'),
    re_path(r'^oncall/email/toggle/$', views.oncall_email_toggle, name='oncall_email_toggle'),
    re_path(r'^oncall/display/save/$', views.oncall_display_save, name='oncall_display_save'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT) + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)