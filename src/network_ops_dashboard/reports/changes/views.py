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
from network_ops_dashboard.reports.changes.models import *
from network_ops_dashboard.reports.changes.scripts.processchangesemail import *

logger = logging.getLogger('network_ops_dashboard.changes')

# Create your views here.

@login_required(login_url='/accounts/login/')
def changes(request):
    secret_search = ['changes_folder', 'changes_extract_folder', 'changes_valid_locations', 'changes_column_map']
    site_secret = SiteSecrets.objects.filter(varname__in=secret_search)
    site_secrets = {s.varname: s.varvalue for s in site_secret}
    for key in secret_search:
        site_secrets.setdefault(key, None)
    missing_keys = [key for key in secret_search if site_secrets[key] is None]
    changes = CompanyChanges.objects.all().order_by('scheduled_start')
    return render(request, 'network_ops_dashboard/reports/changes/home.html', {'changes': changes, 'site_secrets': site_secrets, 'missing_keys': missing_keys })

@login_required(login_url='/accounts/login/')
def changes_update(request):
	ProcessChangesEmails()
	return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))