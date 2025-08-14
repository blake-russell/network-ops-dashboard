from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from django.utils import timezone
from django.db.models import Q
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
from network_ops_dashboard.scripts.cron import ensure_daily_cron, remove_cron

logger = logging.getLogger('network_ops_dashboard.oncall')

# Create your views here. 

@login_required(login_url='/accounts/login/')
def oncall(request):
    circuitmtcemails = (
        CircuitMtcEmail.objects
        .filter(
            Q(status='Planned') | Q(status='Completed') | Q(status='Cancelled') |
            Q(status='Updated') | Q(status='Demand') | Q(status='Emergency')
        )
        .order_by('startdatetime')
        .prefetch_related('circuits__provider')
    )
    providers_with_emails = []
    for provider in CircuitProvider.objects.all():
        emails_qs = circuitmtcemails.filter(circuits__provider=provider).distinct()
        if emails_qs.exists():
            providers_with_emails.append((provider, emails_qs))
    flags = FeatureFlags.load()
    open_incidents = OnCallIncident.objects.filter(status="Open").order_by('-date_created')
    certs = CertExpiry.objects.filter(Q(status='Open')).order_by('expire_date')
    advisories = CiscoAdvisory.objects.filter(Q(status='Open')).order_by('date')
    svc_acts = SvcActExpiry.objects.filter(Q(status='Open')).order_by('expire_date')
    return render(request, 'network_ops_dashboard/oncall/home.html', {'incidents': open_incidents, 'providers_with_emails': providers_with_emails, 'certs': certs, 
                                                                      'advisories': advisories, 'svc_acts': svc_acts, 'feature_flags': flags})

@login_required(login_url='/accounts/login/')
def oncall_incident_log(request):
    closed_incidents = OnCallIncident.objects.filter(status="Closed").order_by('-date_created')
    return render(request, 'network_ops_dashboard/oncall/incident_log.html', {'incidents': closed_incidents })

@login_required(login_url='/accounts/login/')
def oncall_incident_print(request):
    circuitmtcemails = (
        CircuitMtcEmail.objects
        .filter(
            Q(status='Planned') | Q(status='Completed') | Q(status='Cancelled') |
            Q(status='Updated') | Q(status='Demand') | Q(status='Emergency')
        )
        .order_by('startdatetime')
        .prefetch_related('circuits__provider')
    )
    providers_with_emails = []
    for provider in CircuitProvider.objects.all():
        emails_qs = circuitmtcemails.filter(circuits__provider=provider).distinct()
        if emails_qs.exists():
            providers_with_emails.append((provider, emails_qs))
    open_incidents = OnCallIncident.objects.filter(status="Open").order_by('-date_created')
    certs = CertExpiry.objects.filter(Q(status='Open')).order_by('expire_date')
    advisories = CiscoAdvisory.objects.filter(Q(status='Open')).order_by('date')
    svc_acts = SvcActExpiry.objects.filter(Q(status='Open')).order_by('expire_date')
    return render(request, 'network_ops_dashboard/oncall/incident_print.html', {'incidents': open_incidents, 'providers_with_emails': providers_with_emails, 'certs': certs, 
                                                                                'advisories': advisories, 'svc_acts': svc_acts})

@login_required(login_url='/accounts/login/')
def oncall_incident_email(request):
    circuitmtcemails = (
        CircuitMtcEmail.objects
        .filter(
            Q(status='Planned') | Q(status='Completed') | Q(status='Cancelled') |
            Q(status='Updated') | Q(status='Demand') | Q(status='Emergency')
        )
        .order_by('startdatetime')
        .prefetch_related('circuits__provider')
    )
    providers_with_emails = []
    for provider in CircuitProvider.objects.all():
        emails_qs = circuitmtcemails.filter(circuits__provider=provider).distinct()
        if emails_qs.exists():
            providers_with_emails.append((provider, emails_qs))
    open_incidents = OnCallIncident.objects.filter(status="Open").order_by('-date_created')
    certs = CertExpiry.objects.filter(Q(status='Open')).order_by('expire_date')
    advisories = CiscoAdvisory.objects.filter(Q(status='Open')).order_by('date')
    svc_acts = SvcActExpiry.objects.filter(Q(status='Open')).order_by('expire_date')
    return render(request, 'network_ops_dashboard/oncall/incident_email.html', {'incidents': open_incidents, 'providers_with_emails': providers_with_emails, 'certs': certs, 
                                                                                'advisories': advisories, 'svc_acts': svc_acts})

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
    if request.method == 'POST':
        incident.status = 'Closed'
        incident.date_closed = timezone.now()
        incident.user_modified = request.user
        incident.user_closed = request.user
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