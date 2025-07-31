from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, authenticate, get_user_model, update_session_auth_hash
from django.db.models import Q
import logging
from network_ops_dashboard import settings
from network_ops_dashboard.decorators import *
from network_ops_dashboard.asavpn.models import *
from network_ops_dashboard.asavpn.forms import *
from network_ops_dashboard.asavpn.scripts.findvpnusers import *
from network_ops_dashboard.asavpn.scripts.showvpnconnected import *


logger = logging.getLogger('network_ops_dashboard.asavpn')

# Create your views here.

@login_required(login_url='/accounts/login/')
def asavpn_findanddiscouser(request):
    site_secrets = SiteSecrets.objects.filter(varname='asavpn_primary_user')
    if request.method == 'POST':
        form = AsaVpnFindAndDiscoForm(request.POST)
        if form.is_valid():
            targetUser = request.POST['targetUser']
            username1 = request.POST['username1']
            password1 = request.POST['password1']
            targetAction = request.POST['targetAction']
            output = findVPNuser(targetUser, username1, password1, targetAction)
            return render(request, 'network_ops_dashboard/asavpn/findanddiscouser_exec.html', {'output': output})
    else:
        form = AsaVpnFindAndDiscoForm()
    return render(request, 'network_ops_dashboard/asavpn/findanddiscouser.html', {'form': form, 'site_secrets': site_secrets})

@login_required(login_url='/accounts/login/')
def asavpn_findanddiscouser_log(request):
    disco_log = AsaVpnDiscoLog.objects.order_by('-id')[:5]
    detaillist = []
    for log in disco_log:
        detaildict = {
            'pk' : log.pk,
            'username' : log.username,
            'logoutput' : log.logoutput,
            }
        detaillist.append(detaildict)
    return render(request, 'network_ops_dashboard/asavpn/findanddiscouser_log.html', {'detaillist': detaillist})

@login_required(login_url='/accounts/login/')
def asavpn_findanddiscouser_log_all(request):
    disco_log = AsaVpnDiscoLog.objects.all().order_by('-id')
    detaillist = []
    for log in disco_log:
        detaildict = {
            'pk' : log.pk,
            'username' : log.username,
            'logoutput' : log.logoutput,
            }
        detaillist.append(detaildict)
    return render(request, 'network_ops_dashboard/asavpn/findanddiscouser_log_all.html', {'detaillist': detaillist})