from django.shortcuts import render, redirect
from django.contrib.auth.models import Group
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login, authenticate
from django.contrib.admin.views.decorators import staff_member_required
from django.http import HttpResponseRedirect, HttpResponse, JsonResponse
from django.views.decorators.http import require_POST
from django.db.models import Q
from django.utils import timezone
from datetime import timedelta
import logging
from urllib.parse import quote
from network_ops_dashboard.decorators import * # noqa: F403
from network_ops_dashboard.models import * # noqa: F403
from network_ops_dashboard.asavpn.models import AsaVpnConnectedUsers
from network_ops_dashboard.notices.svcactexpiry.models import SvcActExpiry
from network_ops_dashboard.notices.ciscoadvisory.models import CiscoAdvisory
from network_ops_dashboard.notices.certexpiry.models import CertExpiry
from network_ops_dashboard.sdwan.vmanage.models import SdwanSettings
from network_ops_dashboard.sdwan.vmanage.forms import SDWANSettingsForm
from network_ops_dashboard.sdwan.vmanage.scripts.services import top_sites_by_latency
from network_ops_dashboard.forms import * # noqa: F403
from .scripts.changelog_parser import parse_changelog
from .scripts.cron import ensure_minutely_cron, ensure_daily_cron, remove_cron # noqa: F403

logger = logging.getLogger('network_ops_dashboard')

# Create your views here.

def home(request):
    site_settings = SiteSettings.objects.first() # noqa: F405
    return render(request, 'network_ops_dashboard/home.html', {'site_settings': site_settings})

def signup(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get('username')
            raw_password = form.cleaned_data.get('password1')
            user = authenticate(username=username, password=raw_password)
            login(request, user)
            return redirect('dashboard')
    else:
        form = UserCreationForm()
    return render(request, 'registration/signup.html', {'form': form})

@login_required(login_url='/accounts/login/')
def change_password(request):
    return render(request, 'registration/change_password.html')

@login_required(login_url='/accounts/login/')
def change_password_done(request):
    return render(request, 'registration/change_password_done.html')

@login_required(login_url='/accounts/login/')
def themelight(request):
    user = request.user
    newtheme = Group.objects.get(name='themelight')
    oldtheme = Group.objects.get(name='themedark')
    user.groups.remove(oldtheme)
    user.groups.add(newtheme)
    return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))

@login_required(login_url='/accounts/login/')
def themedark(request):
    user = request.user
    newtheme = Group.objects.get(name='themedark')
    oldtheme = Group.objects.get(name='themelight')
    user.groups.remove(oldtheme)
    user.groups.add(newtheme)
    return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))

def public_scripts(request):
    site_settings = SiteSettings.objects.first() # noqa: F405
    return render(request, 'network_ops_dashboard/public_scripts.html', {'site_settings': site_settings})

def protected_media(request, path, document_root=None, show_indexes=False):
    if request.user.is_authenticated and request.user.groups.filter(name='net-admin').exists():
        response = HttpResponse(status=200)
        response['Content-Type'] = ''
        response['X-Accel-Redirect'] = '/protected_media/' + quote(path)
        return response
    else:
        return HttpResponse(status=400)
    
@login_required(login_url='/accounts/login/')
def dashboard(request):
    flags = FeatureFlags.load()
    sdwan_cfg = SdwanSettings.load()
    
    site_settings = SiteSettings.objects.first()
    timecutoff = timezone.now() - timedelta(days=7)

    new_svcacts = SvcActExpiry.objects.filter(Q(created_at__gte=timecutoff) & Q(status="Open"))
    new_certalerts = CertExpiry.objects.filter(Q(created_at__gte=timecutoff) & Q(status="Open"))
    new_ciscoadvisory = CiscoAdvisory.objects.filter(Q(created_at__gte=timecutoff) & Q(status="Open"))
    changelog = parse_changelog()

    # ASA stats only if globally enabled
    card_asa_vpn_stats = []
    if flags.enable_asa_vpn_stats:
        asa_stats = AsaVpnConnectedUsers.objects.all().order_by('name')
        card_asa_vpn_stats = [{"name": a.name, "connected": a.connected, "load": a.load} for a in asa_stats]

    # SDWAN Stats
    sdwan_top_sites = []
    if flags.enable_sdwan_cards and sdwan_cfg.card_enabled and sdwan_cfg.host:
        sdwan_top_sites = top_sites_by_latency(sdwan_cfg.top_n, sdwan_cfg.last_n)

    all_cards = [
        {"id": "changelog", "title": "Recent Site Changes", "required": False},
        {"id": "notifications", "title": "Notifications", "required": False},
        {"id": "asa_vpn_stats", "title": f"ASA: VPN Stats (Last {flags.asa_vpn_interval_minutes}m)", "required": False, "requires_feature": "enable_asa_vpn_stats"},
        {"id": "enable_sdwan_cards", "title": f"vManage: Site Stats (Highest Average Last {sdwan_cfg.last_n}m)", "required": False, "requires_feature": "enable_sdwan_cards"},
    ]

    for c in all_cards:
        req = c.get("requires_feature")
        c["required"] = bool(c.get("required"))
        c["feature_off"] = bool(req) and (not getattr(flags, req, False))

    default_order = [c["id"] for c in all_cards]
    required_ids = {c["id"] for c in all_cards if c["required"]}
    feature_off_ids = {c["id"] for c in all_cards if c["feature_off"]}

    prefs, _ = DashboardPrefs.objects.get_or_create(
        user=request.user,
        defaults={"layout": {"order": default_order, "hidden": []}},
    )

    layout = prefs.layout or {}
    order = [cid for cid in (prefs.layout.get("order") or default_order) if cid in default_order] or default_order
    hidden = set(prefs.layout.get("hidden") or [])
    auto_hidden = set(layout.get("auto_hidden") or [])
    hidden -= required_ids
    hidden |= feature_off_ids

    changed = False
    for c in all_cards:
        cid = c["id"]
        if c["feature_off"]:
            if cid not in hidden:
                hidden.add(cid); changed = True
            if cid not in auto_hidden:
                auto_hidden.add(cid); changed = True
        else:
            if cid in auto_hidden and cid in hidden:
                hidden.remove(cid); changed = True
                auto_hidden.remove(cid); changed = True

    if changed:
        layout["hidden"] = list(hidden)
        layout["auto_hidden"] = list(auto_hidden)
        prefs.layout = layout
        prefs.save(update_fields=["layout"])

    visible_ids = [cid for cid in order if cid not in hidden]

    return render(request, "network_ops_dashboard/dashboard.html", {
        "site_settings": site_settings,
        "new_svcacts": new_svcacts,
        "new_certalerts": new_certalerts,
        "new_ciscoadvisory": new_ciscoadvisory,
        "changelog_entries": changelog,
        "all_cards": all_cards,
        "visible_ids": visible_ids,
        "hidden_ids": hidden,
        "feature_flags": flags,
        "card_asa_vpn_stats": card_asa_vpn_stats,
        "sdwan_cfg": sdwan_cfg,
        "sdwan_top_sites": sdwan_top_sites,
        "sdwan_settings_form": SDWANSettingsForm(instance=SdwanSettings.load())
    })

@login_required(login_url='/accounts/login/')
@require_POST
def dashboard_save_prefs(request):
    import json
    data = json.loads(request.body.decode() or "{}")
    order = data.get("order") or []
    requested_hidden = set(data.get("hidden") or [])

    flags = FeatureFlags.load()
    all_cards = [
        {"id": "notifications", "required": False},
        {"id": "changelog", "required": False},
        {"id": "asa_vpn_stats", "required": False, "requires_feature": "enable_asa_vpn_stats"},
        {"id": "enable_sdwan_cards", "required": False, "requires_feature": "enable_sdwan_cards"},
    ]
    default_order = [c["id"] for c in all_cards]
    required_ids = {c["id"] for c in all_cards if c.get("required")}

    prefs, _ = DashboardPrefs.objects.get_or_create(user=request.user, defaults={"layout": {}})
    layout = prefs.layout or {}

    # Keep existing auto_hidden; don't let user checkboxes clear it
    auto_hidden = set(layout.get("auto_hidden") or [])

    # Sanitize order
    order = [cid for cid in order if cid in default_order] or default_order

    # Apply user choice but never hide required; and always keep auto_hidden hidden
    hidden = requested_hidden - required_ids
    hidden |= auto_hidden

    prefs.layout = {"order": order, "hidden": list(hidden), "auto_hidden": list(auto_hidden)}
    prefs.save()
    return JsonResponse({"ok": True})

@staff_member_required
@require_POST
def dashboard_toggle_asa_vpn_stats(request):
    on = request.POST.get("enabled") == "true"
    flags = FeatureFlags.load()
    flags.enable_asa_vpn_stats = on
    flags.updated_by = request.user
    flags.save()
    if flags.enable_asa_vpn_stats:
        # Ensure cronjob exists.
        ensure_minutely_cron("asa_vpn_stats")
    else:
        # Optionally remove cronjob.
        # remove_cron()
        pass
    return JsonResponse({"ok": True})

@staff_member_required
@require_POST
def dashboard_set_asa_vpn_interval(request):
    minutes = max(int(request.POST.get("minutes", 5)), 1)
    flags = FeatureFlags.load()
    flags.asa_vpn_interval_minutes = minutes
    flags.updated_by = request.user
    flags.save()
    return JsonResponse({"ok": True})

@staff_member_required
@require_POST
def dashboard_toggle_email_processing(request):
    flags = FeatureFlags.load()
    on = request.POST.get("enabled") == "true"
    flags.enable_email_processing = on
    flags.updated_by = request.user
    flags.save()
    key = "process_emails"
    if on and flags.email_processing_time:
        ensure_daily_cron(key, flags.email_processing_time or "06:30")
    else:
        remove_cron(key)
    return JsonResponse({"ok": True})

@staff_member_required
@require_POST
def dashboard_set_email_time(request):
    hhmm = (request.POST.get("time") or "06:30").strip()
    # minimal validation
    try:
        h, m = map(int, hhmm.split(":")); assert 0 <= h <= 23 and 0 <= m <= 59
    except Exception:
        return JsonResponse({"ok": False, "error": "Invalid time"}, status=400)
    flags = FeatureFlags.load()
    flags.email_processing_time = hhmm
    flags.updated_by = request.user
    flags.save()
    key = "process_emails"
    # If enabled, rewrite cron at new time
    if flags.enable_email_processing:
        ensure_daily_cron(key, hhmm)
    return JsonResponse({"ok": True, "time": hhmm})

@staff_member_required
@require_POST
def dashboard_sdwan_settings_save(request):
    flags = FeatureFlags.load()
    enabled = request.POST.get("enabled") in ("true", "on", "1", "yes")

    # feature toggle
    flags.enable_sdwan_cards = enabled
    flags.save(update_fields=["enable_sdwan_cards"])

    # SdwanSettings
    settings_obj = SdwanSettings.load()
    form = SDWANSettingsForm(request.POST, instance=settings_obj)

    top_n_raw = request.POST.get("top_n")
    if top_n_raw:
        try:
            settings_obj.top_n = max(int(top_n_raw), 1)
        except Exception:
            return JsonResponse({"ok": False, "error": "Invalid top_n"}, status=400)

    if form.is_valid():
        s = form.save(commit=False)
        s.card_enabled = enabled
        s.save()
        # cronjob
        if settings_obj.card_enabled:
            ensure_minutely_cron("sdwan_vmanage_stats")
        else:
            # remove_cron()
            pass
        return JsonResponse({"ok": True})
    else:
        return JsonResponse({"ok": False, "errors": form.errors}, status=400)