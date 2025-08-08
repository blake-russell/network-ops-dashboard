"""circuits URL Configuration

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
from . import views

urlpatterns = [
    re_path(r'^$', views.circuitsmtc, name='circuitsmtc'),
    re_path(r'^update/$', views.circuitsmtc_update, name='circuitsmtc_update'),
    re_path(r'^archive/(?P<pk>[0-9]{1,10})/$', views.circuitsmtc_archive, name='circuitsmtc_archive'),
    re_path(r'^circuittag/$', views.circuittag, name='circuittag'),
    re_path(r'^circuittag/add/$', views.circuittag_add, name='circuittag_add'),
    re_path(r'^circuitprovider/$', views.circuitprovider, name='circuitprovider'),
    re_path(r'^circuitprovider/add/$', views.circuitprovider_add, name='circuitprovider_add'),
    re_path(r'^circuitprovider/edit/(?P<pk>[0-9]{1,10})/$', views.circuitprovider_edit, name='circuitprovider_edit'),
    re_path(r'^circuit/$', views.circuit, name='circuit'),
    re_path(r'^circuit/add/$', views.circuit_add, name='circuit_add'),
    re_path(r'^circuit/edit/(?P<pk>[0-9]{1,10})/$', views.circuit_edit, name='circuit_edit'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT) + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)