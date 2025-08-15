from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponseRedirect
from django.contrib.admin.views.decorators import staff_member_required
from django.views.decorators.http import require_POST
import json
import logging
from django.db.models import Q
from network_ops_dashboard.decorators import *
from network_ops_dashboard.models import FeatureFlags
from network_ops_dashboard.inventory.models import Site
from network_ops_dashboard.reports.changes.models import CompanyChanges, CompanyChangesSettings
from network_ops_dashboard.reports.changes.scripts.processchangesemail import ProcessChangesEmails

logger = logging.getLogger('network_ops_dashboard.changes')

# Create your views here.

@login_required(login_url='/accounts/login/')
def changes(request):
    DEFAULT_COLUMN_MAP = {
        "team_name": "Team Name",
        "change_id": "Change#",
        "scheduled_start": "Scheduled Start",
        "scheduled_end": "Scheduled End",
        "class_type": "Change Class",
        "location": "Location",
        "summary": "Change Description",
        "reason": "Change Reason",
        "risk": "Risk Level",
        "group": "Assignment Group",
    }

    settings_obj, _ = CompanyChangesSettings.objects.get_or_create(pk=1)
    if not settings_obj.column_map:
        settings_obj.column_map = DEFAULT_COLUMN_MAP.copy()
        settings_obj.save()

    column_map_json = json.dumps(settings_obj.column_map, indent=2)
    flags = FeatureFlags.load()

    locations = (CompanyChanges.objects
                 .exclude(location__isnull=True).exclude(location__exact="")
                 .order_by('location').values_list('location', flat=True).distinct())
    teams = (CompanyChanges.objects
             .exclude(team_name__isnull=True).exclude(team_name__exact="")
             .order_by('team_name').values_list('team_name', flat=True).distinct())
    groups = (CompanyChanges.objects
              .exclude(group__isnull=True).exclude(group__exact="")
              .order_by('group').values_list('group', flat=True).distinct())

    return render(
        request,
        'network_ops_dashboard/reports/changes/home.html',
        {
            'settings_obj': settings_obj,
            'feature_flags': flags,
            'column_map_json': column_map_json,
            'locations': locations,
            'teams': teams,
            'groups': groups,
        }
    )

@login_required(login_url='/accounts/login/')
def changes_update(request):
	ProcessChangesEmails()
	return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))

@staff_member_required
@require_POST
def save_changes_settings(request):
    import json
    from network_ops_dashboard.inventory.models import Site

    s, _ = CompanyChangesSettings.objects.get_or_create(pk=1)

    s.changes_folder = request.POST.get("changes_folder", s.changes_folder or "")
    s.extract_folder = request.POST.get("extract_folder", s.extract_folder or "")

    try:
        s.header_row = max(int(request.POST.get("header_row", s.header_row or 4)), 1)
    except ValueError:
        pass

    try:
        s.days_before = max(int(request.POST.get("days_before", s.days_before or 1)), 1)
    except ValueError:
        pass

    try:
        s.days_ahead = max(int(request.POST.get("days_ahead", s.days_ahead or 7)), 1)
    except ValueError:
        pass

    # Sites (global) vs custom list
    s.use_sites_for_locations = request.POST.get("use_sites_for_locations") == "on"

    # M2M selection
    site_ids = request.POST.getlist("sites_to_filter")
    if site_ids:
        s.sites_to_filter.set(Site.objects.filter(pk__in=site_ids))
    else:
        s.sites_to_filter.clear()

    # Custom list
    if not s.use_sites_for_locations:
        raw = request.POST.get("custom_valid_locations", "")
        s.custom_valid_locations = [x.strip() for x in raw.split(",") if x.strip()]
    else:
        s.custom_valid_locations = []

    # Column map JSON
    raw_map = request.POST.get("column_map_json", "").strip()
    if raw_map:
        try:
            s.column_map = json.loads(raw_map)
        except Exception:
            # leave existing column_map intact on parse error
            pass

    s.save()
    return JsonResponse({"ok": True})

@login_required(login_url='/accounts/login/')
def changes_data(request):
    location = request.GET.get('location', '').strip()
    team     = request.GET.get('team_name', '').strip()
    group    = request.GET.get('group', '').strip()
    q        = request.GET.get('q', '').strip()

    qs = CompanyChanges.objects.all()

    if location:
        qs = qs.filter(location__iexact=location)
    if team:
        qs = qs.filter(team_name__iexact=team)
    if group:
        qs = qs.filter(group__iexact=group)

    if q:
        qs = qs.filter(
            Q(change_id__icontains=q) |
            Q(summary__icontains=q) |
            Q(reason__icontains=q) |
            Q(location__icontains=q) |
            Q(team_name__icontains=q) |
            Q(group__icontains=q) |
            Q(class_type__icontains=q)
        ).distinct()

    rows = []
    for c in qs.order_by('scheduled_start'):
        meta_str = ""
        if isinstance(c.metadata, dict):
            meta_str = ", ".join(f"{k}: {v}" for k, v in c.metadata.items())

        rows.append({
            "pk": c.pk,
            "change_id": c.change_id or "",
            "location": c.location or "",
            "team_name": c.team_name or "",
            "group": c.group or "",
            "class_type": c.class_type or "",
            "scheduled_start": c.scheduled_start.isoformat() if c.scheduled_start else "",
            "scheduled_end": c.scheduled_end.isoformat() if c.scheduled_end else "",
            "summary": c.summary or "",
            "metadata": meta_str,
        })

    return JsonResponse({"rows": rows})
