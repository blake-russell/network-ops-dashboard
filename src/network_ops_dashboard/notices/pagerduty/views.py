from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.views.decorators.http import require_POST
from django.http import HttpResponse, JsonResponse
import logging
from django.template.loader import render_to_string
from .models import PagerDutySettings, PagerDutyIncident
from .forms import PagerDutySettingsForm
from network_ops_dashboard.models import FeatureFlags
from network_ops_dashboard.scripts.cron import ensure_minutely_cron, ensure_daily_cron, remove_cron # noqa: F403

logger = logging.getLogger('network_ops_dashboard.notices.pagerduty')

# Create your views here.

@login_required(login_url='/accounts/login/')
def pagerduty_card_partial_htmx(request):
    flags = FeatureFlags.load()
    cfg = PagerDutySettings.load()
    rows = []
    if flags.enable_pd_alarms:
        qs = PagerDutyIncident.objects.filter(active=True).order_by("-last_status_at")
        rows = list(qs.values(
            "incident_id","title","status","urgency","service_name","html_url","created_at","assignments"
        )[:cfg.top_n])
    html = render_to_string("network_ops_dashboard/notices/pagerduty/cards.html", {"rows": rows}, request=request)
    return HttpResponse(html)

@staff_member_required
@require_POST
def pagerduty_dashboard_settings_save(request):
    flags = FeatureFlags.load()
    settings_obj = PagerDutySettings.load()
    enabled = request.POST.get("enabled_pagerduty") in ("true", "on", "1", "yes")

    flags.enable_pd_alarms = enabled
    flags.save(update_fields=["enable_pd_alarms"])
    form = PagerDutySettingsForm(request.POST, prefix="pagerduty", instance=settings_obj)

    if not form.is_valid():
        logger.debug(f'PagerDuty Post Errors: {form.errors}')
        return JsonResponse({"ok": False, "errors": form.errors}, status=400)

    form.save().enabled = enabled
    form.save()

    if settings_obj.enabled:
        ensure_minutely_cron("pagerduty_incidents")
    else:
        #try: remove_cron("pagerduty_incidents")
        #except Exception: pass
        pass

    return JsonResponse({"ok": True})