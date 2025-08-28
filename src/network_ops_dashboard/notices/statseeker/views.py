from django.http import HttpResponse, JsonResponse
from django.template.loader import render_to_string
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.views.decorators.http import require_POST
import logging
from .models import StatseekerSettings, StatseekerAlert
from .forms import StatseekerSettingsForm
from network_ops_dashboard.models import FeatureFlags
from network_ops_dashboard.scripts.cron import ensure_minutely_cron, ensure_daily_cron, remove_cron # noqa: F403

logger = logging.getLogger('network_ops_dashboard.notices.statseeker')

# Create your views here.

@login_required(login_url='/accounts/login/')
def statseeker_card_partial_htmx(request):
    cfg = StatseekerSettings.load()
    qs = StatseekerAlert.objects.filter(active=True)
    types = ["DEVICE_DOWN"]
    if cfg.include_if_down:
        types.append("IF_DOWN")
    if cfg.include_if_errors:
        types.append("IF_ERRORS")
    rows = (qs.filter(alert_type__in=types)
          .select_related("device")
          .order_by("-last_seen_at")[:cfg.top_n])
    html = render_to_string("network_ops_dashboard/notices/statseeker/cards.html",
                            {"rows": rows, "cfg": cfg}, request=request)
    return HttpResponse(html)

@staff_member_required
@require_POST
def statseeker_dashboard_settings_save(request):
    flags = FeatureFlags.load()
    settings_obj = StatseekerSettings.load()
    enabled = request.POST.get("enabled_statseeker") in ("true", "on", "1", "yes")

    flags.enable_statseeker_alarms = enabled
    flags.save(update_fields=["enable_statseeker_alarms"])
    form = StatseekerSettingsForm(request.POST, prefix="statseeker", instance=settings_obj)
    if not form.is_valid():
        logger.debug(f'StatSeeker Post Errors: {form.errors}')
        logger.debug(f"{request.POST.get('base_url')}")
        return JsonResponse({"ok": False, "errors": form.errors}, status=400)
    
    form.save().enabled = enabled
    form.save()

    if settings_obj.enabled:
        ensure_minutely_cron("statseeker_alarms")
    else:
        #try: remove_cron("statseeker_alarms")
        #except Exception: pass
        pass

    return JsonResponse({"ok": True})