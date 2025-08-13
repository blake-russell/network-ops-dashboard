from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, authenticate, get_user_model, update_session_auth_hash
from django.http import HttpResponseRedirect
from django.db.models import Q
import logging
from network_ops_dashboard import settings
from network_ops_dashboard.decorators import *
from network_ops_dashboard.models import SiteSecrets, FeatureFlags
from network_ops_dashboard.notices.svcactexpiry.models import *
from network_ops_dashboard.notices.svcactexpiry.scripts.processsvcactexpiryemail import *

logger = logging.getLogger('network_ops_dashboard.svcactexpiry')

# Create your views here.

@login_required(login_url='/accounts/login/')
def svcactexpiry(request):
	site_secrets = SiteSecrets.objects.filter(varname='svcactexpiry_folder')
	svc_acts = SvcActExpiry.objects.filter(Q(status='Open')).order_by('expire_date')
	flags = FeatureFlags.load()
	return render(request, 'network_ops_dashboard/notices/svcactexpiry/home.html', {'svc_acts': svc_acts, 'site_secrets': site_secrets, 'feature_flags': flags})

@login_required(login_url='/accounts/login/')
def svcactexpiry_update(request):
	ProcessSvcActExpiryEmails()
	return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))

@login_required(login_url='/accounts/login/')
def svcactexpiry_archive(request, pk):
	SvcActExpiry.objects.filter(pk=pk).update(status='Closed')
	return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))