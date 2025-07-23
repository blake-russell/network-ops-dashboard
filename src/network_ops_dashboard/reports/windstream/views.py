from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, authenticate, get_user_model, update_session_auth_hash
from django.http import HttpResponseRedirect
from django.db.models import Q
#from django_xhtml2pdf.utils import generate_pdf, pdf_decorator
import logging
from network_ops_dashboard import settings
from network_ops_dashboard.decorators import *
from network_ops_dashboard.reports.windstream.models import *
from network_ops_dashboard.reports.windstream.scripts.processwindstreamemails import *

logger = logging.getLogger('network_ops_dashboard.windstream')

# Create your views here.

@login_required(login_url='/accounts/login/')
def windstream(request):
	# Send entire objects.all to the template then filter out 'Archived' in the jinja template
	wsmtc = WindstreamMtcEmail.objects.filter(Q(status='Planned') | Q(status='Completed') | Q(status='Cancelled') | Q(status='Updated') | Q(status='Demand') | Q(status='Emergency')).order_by('startdatetime')
	site_secrets = SiteSecrets.objects.filter(varname='wstmtcemails_folder')
	return render(request, 'network_ops_dashboard/reports/windstream/home.html', {'wsmtc': wsmtc, 'site_secrets': site_secrets})

@login_required(login_url='/accounts/login/')
def windstream_update(request):
	#circuit_id_list = WindstreamCktID.objects.all()
	circuit_id_list = {
    normalize_circuit_id(c.cktid): c
    for c in WindstreamCktID.objects.all()
	}
	ProcessWindstreamEmails(circuit_id_list)
	return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))

@login_required(login_url='/accounts/login/')
def windstream_archive(request, pk):
	WindstreamMtcEmail.objects.filter(pk=pk).update(status='Archived')
	return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))