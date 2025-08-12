"""network_ops_dashboard URL Configuration

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
    path('admin/', admin.site.urls),
    re_path(r'^$', views.home, name='home'),
    re_path(r'^themelight$', views.themelight, name='themelight'),
    re_path(r'^themedark$', views.themedark, name='themedark'),
    re_path(r'^accounts/', include('django.contrib.auth.urls')),
    re_path(r'^accounts/signup/$', views.signup, name='signup'),
    re_path(r'^accounts/change_password/$', auth_views.PasswordChangeView.as_view(template_name='registration/change_password.html', success_url='done/'), name='change_password'),
    re_path(r'^accounts/change_password/done/$', views.change_password_done, name='change_password_done'),
    re_path(r'^dashboard/$', views.dashboard, name='dashboard'),
    re_path(r'^dashboard/save-prefs/$', views.save_dashboard_prefs, name='save_dashboard_prefs'),
    re_path(r'^public_scripts/$', views.public_scripts, name='public_scripts'),
    re_path(r'^protected_media/(?P<path>.*)', views.protected_media, name='protected_media'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT) + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

urlpatterns += [
    re_path(r'^inventory/', include('network_ops_dashboard.inventory.urls')),
    re_path(r'^f5lb/', include('network_ops_dashboard.f5lb.urls')),
    re_path(r'^asavpn/', include('network_ops_dashboard.asavpn.urls')),
    re_path(r'^apic/', include('network_ops_dashboard.apic.urls')),
    re_path(r'^oncall/', include('network_ops_dashboard.oncall.urls')),
    re_path(r'^reports/changes/', include('network_ops_dashboard.reports.changes.urls')),
    re_path(r'^reports/circuits/', include('network_ops_dashboard.reports.circuits.urls')),
    re_path(r'^notices/certexpiry/', include('network_ops_dashboard.notices.certexpiry.urls')),
    re_path(r'^notices/ciscoadvisory/', include('network_ops_dashboard.notices.ciscoadvisory.urls')),
    re_path(r'^notices/svcactexpiry/', include('network_ops_dashboard.notices.svcactexpiry.urls')),
]