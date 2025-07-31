from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, authenticate, get_user_model, update_session_auth_hash
from django.http import HttpResponseRedirect
from django.db.models import Q
#from django_xhtml2pdf.utils import generate_pdf, pdf_decorator
import logging
from network_ops_dashboard import settings
from network_ops_dashboard.decorators import *
from network_ops_dashboard.models import *
from network_ops_dashboard.notices.ciscoadvisory.models import *
from network_ops_dashboard.notices.ciscoadvisory.scripts.processciscoadvisoryemail import *

logger = logging.getLogger('network_ops_dashboard.ciscoadvisory')

# Create your views here.

@login_required(login_url='/accounts/login/')
def ciscoadvisory(request):
    site_secrets = SiteSecrets.objects.filter(varname='ciscoadvisory_folder')
    advisories = CiscoAdvisory.objects.filter(Q(status='Open')).order_by('date')
    return render(request, 'network_ops_dashboard/notices/ciscoadvisory/home.html', {'advisories': advisories, 'site_secrets': site_secrets })

@login_required(login_url='/accounts/login/')
def ciscoadvisory_update(request):
	ProcessCiscoAdvisoryEmails()
	return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))

@login_required(login_url='/accounts/login/')
def ciscoadvisory_archive(request, pk):
	CiscoAdvisory.objects.filter(pk=pk).update(status='Closed')
	return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))