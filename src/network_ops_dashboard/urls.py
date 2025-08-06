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
    url(r'^$', views.home, name='home'),
    url(r'^themelight$', views.themelight, name='themelight'),
    url(r'^themedark$', views.themedark, name='themedark'),
    url(r'^accounts/', include('django.contrib.auth.urls')),
    url(r'^accounts/signup/$', views.signup, name='signup'),
    url(r'^accounts/change_password/$', auth_views.PasswordChangeView.as_view(template_name='registration/change_password.html', success_url='done/'), name='change_password'),
    url(r'^accounts/change_password/done/$', views.change_password_done, name='change_password_done'),
    url(r'^dashboard/$', views.dashboard, name='dashboard'),
    url(r'^public_scripts/$', views.public_scripts, name='public_scripts'),
    url(r'^protected_media/(?P<path>.*)', views.protected_media, name='protected_media'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT) + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

urlpatterns += [
    url(r'^inventory/', include('network_ops_dashboard.inventory.urls')),
    url(r'^f5lb/', include('network_ops_dashboard.f5lb.urls')),
    url(r'^asavpn/', include('network_ops_dashboard.asavpn.urls')),
    url(r'^apic/', include('network_ops_dashboard.apic.urls')),
    url(r'^oncall/', include('network_ops_dashboard.oncall.urls')),
    url(r'^reports/changes/', include('network_ops_dashboard.reports.changes.urls')),
    url(r'^reports/circuits/', include('network_ops_dashboard.reports.circuits.urls')),
    url(r'^notices/certexpiry/', include('network_ops_dashboard.notices.certexpiry.urls')),
    url(r'^notices/ciscoadvisory/', include('network_ops_dashboard.notices.ciscoadvisory.urls')),
    url(r'^notices/svcactexpiry/', include('network_ops_dashboard.notices.svcactexpiry.urls')),
]