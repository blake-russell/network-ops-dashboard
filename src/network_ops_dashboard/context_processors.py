# network_ops_dashboard/context_processors.py
from network_ops_dashboard.models import SiteSettings

def site_settings_context(request):
    return {
        'site_settings': SiteSettings.objects.first()
    }