from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.template.loader import render_to_string
from django.contrib.admin.views.decorators import staff_member_required
from django.http import HttpResponse, JsonResponse
from django.views.decorators.http import require_POST
import logging
from network_ops_dashboard.models import FeatureFlags
from .models import SdwanSettings
from .forms import SDWANSettingsForm
from .scripts.services import top_sites_by_latency
from network_ops_dashboard.scripts.cron import ensure_minutely_cron, ensure_daily_cron, remove_cron # noqa: F403

logger = logging.getLogger('network_ops_dashboard.sdwan.vmanage')

# Create your views here.

@login_required(login_url='/accounts/login/')
def sdwan_card_partial_json(request):
    cfg = SdwanSettings.load()
    data = top_sites_by_latency(cfg.top_n, cfg.last_n)
    return JsonResponse({"rows": data})

@login_required(login_url='/accounts/login/')
def sdwan_card_partial_htmx(request):
    cfg = SdwanSettings.load()
    rows = top_sites_by_latency(cfg.top_n, cfg.last_n)
    html = render_to_string(
        "network_ops_dashboard/sdwan/vmanage/cards.html",
        {"sdwan_top_sites": rows}, request=request)
    return HttpResponse(html)

@staff_member_required
@require_POST
def sdwan_dashboard_settings_save(request):
    flags = FeatureFlags.load()
    settings_obj = SdwanSettings.load()
    enabled = request.POST.get("enabled_sdwan") in ("true", "on", "1", "yes")
    interval_raw = (request.POST.get("sdwan_interval") or "").strip()
    try:
        interval = max(1, int(interval_raw)) if interval_raw else flags.sdwan_interval_minutes or 5
    except ValueError:
        return JsonResponse({"ok": False, "error": "Invalid interval"}, status=400)

    flags.enable_sdwan_cards, flags.sdwan_interval_minutes = enabled, interval
    flags.save(update_fields=["enable_sdwan_cards", "sdwan_interval_minutes"])
    form = SDWANSettingsForm(request.POST, prefix="sdwan", instance=settings_obj)
    if not form.is_valid():
        logger.debug(f'SDWAN vManage Post Errors: {form.errors}')
        return JsonResponse({"ok": False, "errors": form.errors}, status=400)

    form.save().card_enabled = enabled
    form.save()

    if settings_obj.card_enabled:
        ensure_minutely_cron("sdwan_vmanage_stats")
    else:
        #try: remove_cron("sdwan_vmanage_stats")
        #except Exception: pass
        pass

    return JsonResponse({"ok": True})