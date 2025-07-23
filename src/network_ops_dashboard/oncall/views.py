from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, authenticate, get_user_model, update_session_auth_hash
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from django.utils import timezone
from django.db.models import Q
import logging
from network_ops_dashboard import settings
from network_ops_dashboard.decorators import *
from network_ops_dashboard.models import *
from network_ops_dashboard.inventory.models import *
from network_ops_dashboard.reports.windstream.models import *
from network_ops_dashboard.oncall.models import *
from network_ops_dashboard.oncall.forms import *

logger = logging.getLogger('network_ops_dashboard.oncall')

# Create your views here. 

@login_required(login_url='/accounts/login/')
def oncall(request):
    open_incidents = OnCallIncident.objects.filter(status="Open").order_by('-date_created')
    wsmtc = WindstreamMtcEmail.objects.filter(Q(status='Planned') | Q(status='Updated') | Q(status='Emergency') | \
                                              Q(status='Demand') | Q(status='Postponed') | Q(status='Cancelled') | \
                                                Q(status='Completed')).order_by('startdatetime')
    return render(request, 'network_ops_dashboard/oncall/home.html', {'incidents': open_incidents, 'wsmtc': wsmtc})

@login_required(login_url='/accounts/login/')
def oncall_incident_log(request):
    closed_incidents = OnCallIncident.objects.filter(status="Closed").order_by('-date_created')
    return render(request, 'network_ops_dashboard/oncall/incident_log.html', {'incidents': closed_incidents})

@login_required(login_url='/accounts/login/')
def oncall_incident_print(request):
    open_incidents = OnCallIncident.objects.filter(status="Open").order_by('-date_created')
    wsmtc = WindstreamMtcEmail.objects.filter(Q(status='Planned') | Q(status='Updated') | Q(status='Emergency') | \
                                              Q(status='Demand') | Q(status='Postponed') | Q(status='Cancelled') | \
                                                Q(status='Completed')).order_by('startdatetime')
    return render(request, 'network_ops_dashboard/oncall/incident_print.html', {'incidents': open_incidents, 'wsmtc': wsmtc})

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

