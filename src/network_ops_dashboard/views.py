from django.shortcuts import render, redirect
from django.contrib.auth.models import User, Group
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login, authenticate
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
from network_ops_dashboard.forms import * # noqa: F403
from .scripts.changelog_parser import parse_changelog

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
    site_settings = SiteSettings.objects.first()
    asa_stats = AsaVpnConnectedUsers.objects.all().order_by('name')
    timecutoff = timezone.now() - timedelta(days=7)
    new_svcacts = SvcActExpiry.objects.filter(Q(created_at__gte=timecutoff) & Q(status="Open"))
    new_certalerts = CertExpiry.objects.filter(Q(created_at__gte=timecutoff) & Q(status="Open"))
    new_ciscoadvisory = CiscoAdvisory.objects.filter(Q(created_at__gte=timecutoff) & Q(status="Open"))
    changelog = parse_changelog()
    asastats = [{"name": a.name, "connected": a.connected, "load": a.load} for a in asa_stats]

    all_cards = [
        {"id": "notifications", "title": "Notifications"},
        {"id": "vpn_stats", "title": "VPN Stats (5m interval)"},
        {"id": "changelog", "title": "Recent Site Changes"},
        # add future cards here
    ]

    prefs, _ = DashboardPrefs.objects.get_or_create(
        user=request.user,
        defaults={"layout": {"order": [c["id"] for c in all_cards], "hidden": []}},
    )
    visible_ids = prefs.enabled_order(all_cards)

    return render(request, "network_ops_dashboard/dashboard.html", {
        "site_settings": site_settings,
        "asastats": asastats,
        "new_svcacts": new_svcacts,
        "new_certalerts": new_certalerts,
        "new_ciscoadvisory": new_ciscoadvisory,
        "changelog_entries": changelog,
        "all_cards": all_cards,
        "visible_ids": visible_ids,
        "hidden_ids": set(prefs.layout.get("hidden", [])),
    })

@login_required(login_url='/accounts/login/')
@require_POST
def save_dashboard_prefs(request):
    import json
    data = json.loads(request.body.decode() or "{}")
    order = data.get("order") or []
    hidden = data.get("hidden") or []
    prefs, _ = DashboardPrefs.objects.get_or_create(user=request.user, defaults={"layout": {}})
    prefs.layout = {"order": order, "hidden": hidden}
    prefs.save()
    return JsonResponse({"ok": True})