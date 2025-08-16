from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from django.utils import timezone
from datetime import timedelta
import logging
from network_ops_dashboard.decorators import *
from network_ops_dashboard.models import *
from network_ops_dashboard.inventory.models import *
from network_ops_dashboard.reports.circuits.models import *
from network_ops_dashboard.notices.certexpiry.models import *
from network_ops_dashboard.notices.ciscoadvisory.models import *
from network_ops_dashboard.notices.svcactexpiry.models import *
from network_ops_dashboard.oncall.models import *
from network_ops_dashboard.oncall.forms import *
from network_ops_dashboard.models import FeatureFlags
from network_ops_dashboard.scripts.cron import ensure_daily_cron, ensure_weekly_cron, remove_cron

logger = logging.getLogger('network_ops_dashboard.oncall')

def build_providers_with_emails(settings_obj: OnCallSettings):
    base = (CircuitMtcEmail.objects
            .filter(status__in=['Planned','Completed','Cancelled','Updated','Demand','Emergency'])
            .order_by('startdatetime')
            .prefetch_related('circuits__provider', 'circuits__tag'))

    selected_tags = list(settings_obj.circuit_tags.values_list('pk', flat=True))
    if selected_tags:
        base = base.filter(circuits__tag__in=selected_tags).distinct()

    providers_with_emails = []
    for provider in CircuitProvider.objects.all():
        emails_qs = base.filter(circuits__provider=provider).distinct()
        if emails_qs.exists():
            providers_with_emails.append((provider, emails_qs))
    return providers_with_emails

def _incidents_for_report(settings_obj):
    days = max(settings_obj.report_window_days or 7, 1)
    since = timezone.now() - timedelta(days=days)
    qs = OnCallIncident.objects.filter(date_created__gte=since).exclude(status="Archived")
    if settings_obj.show_closed_in_report:
        return qs.order_by('-date_created')
    else:
        return qs.filter(status="Open").order_by('-date_created')
    
# Create your views here. 

@login_required(login_url='/accounts/login/')
def oncall(request):
    settings_obj = OnCallSettings.load()
    days = ["Mon", "Tue", "Wed", "Thur", "Fri", "Sat", "Sun"]

    providers_with_emails = build_providers_with_emails(settings_obj) if settings_obj.show_scheduled_maintenance else []
    incidents = _incidents_for_report(settings_obj)
    #incidents = OnCallIncident.objects.filter(status="Open").order_by('-date_created')

    certs     = CertExpiry.objects.filter(status='Open').order_by('expire_date') if settings_obj.show_cert_expiry else CertExpiry.objects.none()
    advisories= CiscoAdvisory.objects.filter(status='Open').order_by('date')     if settings_obj.show_field_advisories else CiscoAdvisory.objects.none()
    svc_acts  = SvcActExpiry.objects.filter(status='Open').order_by('expire_date') if settings_obj.show_svcacct_expiry else SvcActExpiry.objects.none()

    return render(request, 'network_ops_dashboard/oncall/home.html', {
        'incidents': incidents,
        'providers_with_emails': providers_with_emails,
        'certs': certs,
        'advisories': advisories,
        'svc_acts': svc_acts,
        'days': days,
        'feature_flags': FeatureFlags.load(),
        'tags': CircuitTag.objects.order_by('name'),
        'oncall_settings': settings_obj,
    })

@login_required(login_url='/accounts/login/')
def oncall_incident_log(request):
    closed_incidents = OnCallIncident.objects.filter(status="Archived").order_by('-date_created')
    return render(request, 'network_ops_dashboard/oncall/incident_log.html', {'incidents': closed_incidents })

@login_required(login_url='/accounts/login/')
def oncall_incident_print(request):
    settings_obj = OnCallSettings.load()
    providers_with_emails = build_providers_with_emails(settings_obj) if settings_obj.show_scheduled_maintenance else []
    #incidents = OnCallIncident.objects.filter(status="Open").order_by('-date_created')
    incidents = _incidents_for_report(settings_obj)
    certs = CertExpiry.objects.filter(status='Open').order_by('expire_date') if settings_obj.show_cert_expiry else CertExpiry.objects.none()
    advisories = CiscoAdvisory.objects.filter(status='Open').order_by('date')     if settings_obj.show_field_advisories else CiscoAdvisory.objects.none()
    svc_acts = SvcActExpiry.objects.filter(status='Open').order_by('expire_date') if settings_obj.show_svcacct_expiry else SvcActExpiry.objects.none()

    return render(request, 'network_ops_dashboard/oncall/incident_print.html', {
        'incidents': incidents,
        'providers_with_emails': providers_with_emails,
        'certs': certs,
        'advisories': advisories,
        'svc_acts': svc_acts,
        'oncall_settings': settings_obj,
    })

@login_required(login_url='/accounts/login/')
def oncall_incident_email(request):
    settings_obj = OnCallSettings.load()
    providers_with_emails = build_providers_with_emails(settings_obj) if settings_obj.show_scheduled_maintenance else []
    #incidents = OnCallIncident.objects.filter(status="Open").order_by('-date_created')
    incidents = _incidents_for_report(settings_obj)
    certs = CertExpiry.objects.filter(status='Open').order_by('expire_date') if settings_obj.show_cert_expiry else CertExpiry.objects.none()
    advisories = CiscoAdvisory.objects.filter(status='Open').order_by('date')     if settings_obj.show_field_advisories else CiscoAdvisory.objects.none()
    svc_acts = SvcActExpiry.objects.filter(status='Open').order_by('expire_date') if settings_obj.show_svcacct_expiry else SvcActExpiry.objects.none()

    return render(request, 'network_ops_dashboard/oncall/incident_email.html', {
        'incidents': incidents,
        'providers_with_emails': providers_with_emails,
        'certs': certs,
        'advisories': advisories,
        'svc_acts': svc_acts,
        'oncall_settings': settings_obj,
    })

@require_POST
@login_required(login_url='/accounts/login/')
def oncall_update_incident_log(request, pk):
    incident = get_object_or_404(OnCallIncident, pk=pk)
    incident.log = request.POST.get('log', incident.log)
    incident.user_modified = request.user
    incident.save()
    return JsonResponse({'success': True})

@login_required(login_url='/accounts/login/')
def oncall_close_incident(request, incident_id):
    incident = get_object_or_404(OnCallIncident, pk=incident_id)
    if request.method == 'POST' and incident.status == 'Open':
        incident.status = 'Closed'
        incident.date_closed = timezone.now()
        incident.user_modified = request.user
        incident.user_closed = request.user
        incident.save()
    elif request.method == 'POST' and incident.status == 'Closed':
        incident.status = 'Archived'
        incident.user_modified = request.user
        incident.save()
    return redirect('oncall')

@login_required(login_url='/accounts/login/')
def oncall_open_incident(request, incident_id):
    incident = get_object_or_404(OnCallIncident, pk=incident_id)
    if request.method == 'POST':
        incident.status = 'Open'
        incident.user_modified = request.user
        incident.save()
    return redirect('oncall_incident_log')

@login_required(login_url='/accounts/login/')
def oncall_add_incident(request):
    if request.method == 'POST':
        form = OnCallIncidentForm(request.POST)
        if form.is_valid():
            incident = form.save(commit=False)
            incident.status = 'Open'
            incident.date_opened = timezone.now()
            incident.user_created = request.user
            form.save()
            return redirect('oncall')
    else:
        form = OnCallIncidentForm()
    return render(request, 'network_ops_dashboard/oncall/add_incident.html', {'form': form})

@staff_member_required
@require_POST
def oncall_email_save_settings(request):
    flags = FeatureFlags.load()
    flags.oncall_email_to = request.POST.get("recipients", flags.oncall_email_to or "")
    hhmm = (request.POST.get("send_time") or "08:30").strip()
    try:
        h, m = map(int, hhmm.split(":")); assert 0 <= h <= 23 and 0 <= m <= 59
    except Exception:
        return JsonResponse({"ok": False, "error": "Invalid time"}, status=400)
    flags.oncall_email_time = hhmm
    flags.updated_by = request.user
    flags.save()
    key = "send_oncall_email"
    if flags.oncall_email_time:
        ensure_daily_cron(key, hhmm)
    return JsonResponse({"ok": True, "time": hhmm})

@staff_member_required
@require_POST
def oncall_email_toggle(request):
    flags = FeatureFlags.load()
    on = request.POST.get("enabled") == "true"
    flags.enable_oncall_email = on
    flags.updated_by = request.user
    flags.save()
    key = "send_oncall_email"
    if on and flags.oncall_email_time:
        ensure_daily_cron(key, flags.oncall_email_time or "8:30")
    else:
        remove_cron(key)
    return JsonResponse({"ok": True})

@staff_member_required
@require_POST
def oncall_display_save(request):
    s = OnCallSettings.load()

    s.show_scheduled_maintenance = (request.POST.get("show_scheduled_maintenance") == "on")
    s.show_field_advisories      = (request.POST.get("show_field_advisories") == "on")
    s.show_cert_expiry           = (request.POST.get("show_cert_expiry") == "on")
    s.show_svcacct_expiry        = (request.POST.get("show_svcacct_expiry") == "on")

    tag_ids = request.POST.getlist("circuit_tags")

    try:
        s.report_window_days = max(int(request.POST.get("report_window_days", s.report_window_days or 7)), 1)
    except Exception:
        pass
    s.show_closed_in_report = (request.POST.get("show_closed_in_report") == "on")

    s.auto_archive_enabled   = (request.POST.get("auto_archive_enabled") == "on")
    s.auto_archive_frequency = request.POST.get("auto_archive_frequency", s.auto_archive_frequency or "weekly")
    s.auto_archive_time      = (request.POST.get("auto_archive_time") or s.auto_archive_time or "08:30")
    try:
        s.auto_archive_weekday = int(request.POST.get("auto_archive_weekday", s.auto_archive_weekday or 0))
    except Exception:
        pass

    s.save()

    if tag_ids:
        s.circuit_tags.set(CircuitTag.objects.filter(pk__in=tag_ids))
    else:
        s.circuit_tags.clear()

    key = "archive_oncall_closed"
    if s.auto_archive_enabled:
        if s.auto_archive_frequency == "daily":
            ensure_daily_cron(key, s.auto_archive_time)
        else:
            ensure_weekly_cron(key, s.auto_archive_time, s.auto_archive_weekday)
    else:
        remove_cron(key)

    return JsonResponse({"ok": True})