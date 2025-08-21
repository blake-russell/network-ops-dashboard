from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.template.loader import render_to_string
from django.http import JsonResponse, HttpResponse
import logging
from network_ops_dashboard.sdwan.vmanage.models import SdwanSettings
from network_ops_dashboard.sdwan.vmanage.scripts.services import top_sites_by_latency

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