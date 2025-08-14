# network_ops_dashboard/context_processors.py
from network_ops_dashboard.models import SiteSettings
from django.contrib.auth import get_user_model
from django.db.models import Count

def site_settings_context(request):
    return {
        'site_settings': SiteSettings.objects.first()
    }

def user_group_health(request):
    try:
        if not request.user.is_authenticated or not (request.user.is_staff or request.user.is_superuser):
            return {}
        User = get_user_model()
        qs = (
            User.objects
            .filter(is_superuser=False)
            .annotate(num_groups=Count('groups'))
            .filter(num_groups=0)
            .order_by('username')
        )
        return {
            "ungrouped_users_count": qs.count(),
            "ungrouped_users_sample": list(qs.values_list("username", flat=True)[:5]),
        }
    except Exception:
        # Fail-quietly so templates never break
        return {}