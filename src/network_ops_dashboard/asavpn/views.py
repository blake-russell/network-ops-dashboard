from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.views.decorators.http import require_POST
from django.template.loader import render_to_string
from django.http import HttpResponse, JsonResponse
import logging
from django.db.models import Q, IntegerField, Value, Case, When
from django.db.models.functions import Cast
from network_ops_dashboard.decorators import *
from network_ops_dashboard.asavpn.models import *
from network_ops_dashboard.asavpn.forms import *
from network_ops_dashboard.asavpn.scripts.findvpnusers import *
from network_ops_dashboard.asavpn.scripts.showvpnconnected import *
from network_ops_dashboard.scripts.cron import ensure_minutely_cron, ensure_daily_cron, remove_cron # noqa: F403


logger = logging.getLogger('network_ops_dashboard.asavpn')

# Create your views here.

@login_required(login_url='/accounts/login/')
def asavpn_findanddiscouser(request):
    if request.method == 'POST':
        form = AsaVpnFindAndDiscoForm(request.POST)
        if form.is_valid():
            targetUser = request.POST['targetUser']
            username1 = request.POST['username1']
            password1 = request.POST['password1']
            targetAction = form.cleaned_data['targetAction']
            targetDeviceTag = form.cleaned_data['targetDeviceTag']
            verifySSL = form.cleaned_data['verifySSL']
            assert isinstance(verifySSL, bool)
            assert isinstance(targetAction, bool)
            output = findVPNuser(targetUser, targetAction, targetDeviceTag.name, verifySSL, username1, password1)
            return render(request, 'network_ops_dashboard/asavpn/findanddiscouser_exec.html', {'output': output})
    else:
        form = AsaVpnFindAndDiscoForm()
    return render(request, 'network_ops_dashboard/asavpn/findanddiscouser.html', {'form': form})

@login_required(login_url='/accounts/login/')
def asavpn_findanddiscouser_log(request):
    disco_log = AsaVpnDiscoLog.objects.order_by('-id')[:5]
    detaillist = []
    for log in disco_log:
        detaildict = {
            'pk' : log.pk,
            'username' : log.username,
            'logoutput' : log.logoutput,
            }
        detaillist.append(detaildict)
    return render(request, 'network_ops_dashboard/asavpn/findanddiscouser_log.html', {'detaillist': detaillist})

@login_required(login_url='/accounts/login/')
def asavpn_findanddiscouser_log_all(request):
    disco_log = AsaVpnDiscoLog.objects.all().order_by('-id')
    detaillist = []
    for log in disco_log:
        detaildict = {
            'pk' : log.pk,
            'username' : log.username,
            'logoutput' : log.logoutput,
            }
        detaillist.append(detaildict)
    return render(request, 'network_ops_dashboard/asavpn/findanddiscouser_log_all.html', {'detaillist': detaillist})

@login_required(login_url='/accounts/login/')
def asavpn_card_partial_htmx(request):
    flags = FeatureFlags.load()
    asa_settings = AsaVpnSettings.load()
    if flags.enable_asa_vpn_stats:
        n = max(int(asa_settings.top_n or 10), 1)
        asa_stats = (
            AsaVpnConnectedUsers.objects
            .annotate(conn_int=Case(
                When(connected__regex=r'^\d+$', then=Cast('connected', IntegerField())),
                default=Value(0),
                output_field=IntegerField(),
                )
            )
            .order_by('-conn_int', 'name')[:n]
        )
        card_asa_vpn_stats = [{"name": a.name, "connected": a.connected, "load": a.load} for a in asa_stats]
    else:
        card_asa_vpn_stats = []
    html = render_to_string(
        "network_ops_dashboard/asavpn/cards.html",
        {"card_asa_vpn_stats": card_asa_vpn_stats}, request=request)
    return HttpResponse(html)

@staff_member_required
@require_POST
def asavpn_dashboard_settings_save(request):
    flags = FeatureFlags.load()

    enabled = request.POST.get("enable_asavpn_stats") in ("true", "on", "1", "yes")
    interval_raw = (request.POST.get("asavpn_interval") or "").strip()
    try:
        interval = max(1, int(interval_raw)) if interval_raw else flags.asa_vpn_interval_minutes or 5
    except ValueError:
        return JsonResponse({"ok": False, "error": "Invalid interval"}, status=400)

    flags.enable_asa_vpn_stats = enabled
    flags.asa_vpn_interval_minutes = interval
    flags.updated_by = request.user
    flags.save(update_fields=["enable_asa_vpn_stats", "asa_vpn_interval_minutes", "updated_by"])

    if enabled:
        ensure_minutely_cron("asa_vpn_stats")
    else:
        #try: remove_cron("asa_vpn_stats")
        #except Exception: pass
        pass

    cfg = AsaVpnSettings.load()
    form = AsaVpnSettingsForm(request.POST, prefix="asa", instance=cfg)
    if not form.is_valid():
        return JsonResponse({"ok": False, "errors": form.errors}, status=400)
    cfg = form.save()

    return JsonResponse({
        "ok": True,
        "feature_flags": {
            "enable_asa_vpn_stats": flags.enable_asa_vpn_stats,
            "asa_vpn_interval_minutes": flags.asa_vpn_interval_minutes,
        },
        "asa_settings": {
            "device_tag": cfg.device_tag,
            "top_n": cfg.top_n,
            "verify_ssl": cfg.verify_ssl,
        }
    })