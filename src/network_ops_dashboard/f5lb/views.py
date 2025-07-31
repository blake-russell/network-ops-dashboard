from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, authenticate, get_user_model, update_session_auth_hash
from django.http import HttpResponseRedirect, HttpResponse, StreamingHttpResponse, JsonResponse
from django.db.models import Q
import logging
from network_ops_dashboard import settings
from network_ops_dashboard.decorators import *
from network_ops_dashboard.models import *
from network_ops_dashboard.inventory.models import *
from network_ops_dashboard.f5lb.models import *
from network_ops_dashboard.f5lb.forms import *
from network_ops_dashboard.f5lb.scripts.vipcertrenew import RunF5LBMopVipCertRenew
from network_ops_dashboard.f5lb.scripts.loadconfiglistoptions import LoadF5LBConfigListsOptions
import json

logger = logging.getLogger('network_ops_dashboard.f5lb')

# Create your views here.

@login_required(login_url='/accounts/login/')
def f5lb_vipcertrenew(request):
    # SiteSecrets.objects() check
    secret_search = ['f5lb_primary_user', 'f5lb_secondary_user', 'backLink_f5lb_vipcertrenew', 'f5lb_temp_devicecheck', 'f5lb_temp_devicecheck']
    site_secret = SiteSecrets.objects.filter(varname__in=secret_search)
    site_secrets = {s.varname: s.varvalue for s in site_secret}
    for key in secret_search:
        site_secrets.setdefault(key, None)
    missing_keys = [key for key in secret_search if site_secrets[key] is None]
    # Instead of sending entire objects.all do filtering here in view then display entire dict in template.
    f5lb_mops_all = F5LBMopVipCertRenew.objects.filter(Q(status='Planned') | Q(status='Completed') | Q(status='Cancelled') | Q(status='Running')).order_by('status')
    detaillist = []
    load_all = '4096' ### Used as a arbitrary value to send to f5lb_loadconfigoptions in order to run against F5LBConfigOptions.objects.all()
    for mop in f5lb_mops_all:
        detaildict = {
            'pk' : mop.pk,
            'name' : mop.name,
            'status' : mop.status,
            'device' : mop.device,
            'virtual_server' : mop.virtual_server,
            'ssl_policy' : mop.ssl_policy,
            'cert_name' : mop.cert_name,
            'cert_key_name' : mop.cert_key_name,
            'cert_file' : mop.cert_file,
            }
        detaillist.append(detaildict)
    return render(request, 'network_ops_dashboard/f5lb/mop_vipcertrenew.html', {'detaillist': detaillist, 'load_all': load_all, 'site_secrets': site_secrets, 'missing_keys': missing_keys })

@login_required(login_url='/accounts/login/')
def f5lb_vipcertrenew_edit(request, pk):
    f5lb_mop = get_object_or_404(F5LBMopVipCertRenew, pk=pk)
    if request.method == 'POST':
        form = F5LBMopVipCertRenewForm(request.POST, request.FILES, instance=f5lb_mop)
        if form.is_valid():
            f5lb_mop = form.save(commit=True)
            f5lb_mop.save()
            return redirect('f5lb_vipcertrenew')
    else:
        # SiteSecrets.objects() check
        secret_search = ['f5lb_primary_user', 'f5lb_secondary_user', 'backLink_f5lb_vipcertrenew', 'f5lb_temp_devicecheck', 'f5lb_temp_devicecheck']
        site_secret = SiteSecrets.objects.filter(varname__in=secret_search)
        site_secrets = {s.varname: s.varvalue for s in site_secret}
        for key in secret_search:
            site_secrets.setdefault(key, None)
        missing_keys = [key for key in secret_search if site_secrets[key] is None]
        form = F5LBMopVipCertRenewForm(instance=f5lb_mop)
    return render(request, 'network_ops_dashboard/f5lb/mop_vipcertrenew_edit.html', {'form': form, 'site_secrets': site_secrets, 'missing_keys': missing_keys })

@login_required(login_url='/accounts/login/')
def f5lb_vipcertrenew_add(request):
    if request.method == 'POST':
        form = F5LBMopVipCertRenewForm(request.POST, request.FILES)
        if form.is_valid():
            f5lb_mop = form.save(commit=False)
            f5lb_mop.save()
            return redirect('f5lb_vipcertrenew')
    else:
        # SiteSecrets.objects() check
        secret_search = ['f5lb_primary_user', 'f5lb_secondary_user', 'backLink_f5lb_vipcertrenew', 'f5lb_temp_devicecheck', 'f5lb_temp_devicecheck']
        site_secret = SiteSecrets.objects.filter(varname__in=secret_search)
        site_secrets = {s.varname: s.varvalue for s in site_secret}
        for key in secret_search:
            site_secrets.setdefault(key, None)
        missing_keys = [key for key in secret_search if site_secrets[key] is None]
        form = F5LBMopVipCertRenewForm()
    return render(request, 'network_ops_dashboard/f5lb/mop_vipcertrenew_add.html', {'form': form, 'site_secrets': site_secrets, 'missing_keys': missing_keys})

@login_required(login_url='/accounts/login/')
def f5lb_vipcertrenew_archive(request, pk):
    mop_entry = get_object_or_404(F5LBMopVipCertRenew, pk=pk)
    mop_entry.cert_key_file.delete()
    mop_entry.status = 'Closed'
    mop_entry.save()
    return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))

@login_required(login_url='/accounts/login/')
def f5lb_vipcertrenew_run(request, pk):
    F5LBMopVipCertRenew.objects.filter(pk=pk).update(status='Running')
    mop = F5LBMopVipCertRenew.objects.filter(pk=pk)
    try:
        f5lb_temp_devicecheck = json.loads(SiteSecrets.objects.filter(varname='f5lb_temp_devicecheck')[0].varvalue)
        if any(check in mop[0].device.name for check in f5lb_temp_devicecheck):
            creds_name = SiteSecrets.objects.filter(varname='f5lb_secondary_user')[0].varvalue
            creds = NetworkCredential.objects.filter(username_lookup=creds_name)
        else:
            creds_name = SiteSecrets.objects.filter(varname='f5lb_primary_user')[0].varvalue
            creds = NetworkCredential.objects.filter(username_lookup=creds_name)
    except Exception as e:
        logger.exception(f"No 'f5lb_primary_user'/'f5lb_primary_user'/'f5lb_temp_devicecheck' set in SiteSecrets.objects(): {e}")
        response = HttpResponse(f"No 'f5lb_primary_user'/'f5lb_primary_user'/'f5lb_temp_devicecheck' set in SiteSecrets.objects(): {e}", content_type='text/html')
        return response
    reqUser = User.objects.get(username=request.user)
    if User.objects.filter(pk=reqUser.pk, groups__name='themelight').exists():
        theme = 'themelight'
    else:
        theme = 'themedark'
    response = StreamingHttpResponse(RunF5LBMopVipCertRenew(mop, reqUser.username, theme, creds), content_type='text/html')
    response['X-Accel-Buffering'] = 'no'  # Disable buffering in nginx
    response['Cache-Control'] = 'no-cache'  # Ensure clients don't cache the data
    response['Transfer-Encoding'] = 'chunked'
    return response

@login_required(login_url='/accounts/login/')
def f5lb_loadconfigoptions(request, device_id):
    if device_id == '4096':
        deviceList = F5LBConfigOptions.objects.all()
    else:
        deviceList = F5LBConfigOptions.objects.filter(device__id=device_id)
    try:
        creds_name = SiteSecrets.objects.filter(varname='f5lb_primary_user')[0].varvalue
        creds2_name = SiteSecrets.objects.filter(varname='f5lb_secondary_user')[0].varvalue
        creds = NetworkCredential.objects.filter(username_lookup=creds_name)
        creds2 = NetworkCredential.objects.filter(username_lookup=creds2_name)
    except Exception as e:
        logger.exception(f"No 'f5lb_primary_user' or 'f5lb_secondary_user' set in SiteSecrets.objects(): {e}")
        response = HttpResponse(f"No 'f5lb_primary_user' or 'f5lb_secondary_user' set in SiteSecrets.objects(): {e}", content_type='text/html')
        return response
    reqUser = User.objects.get(username=request.user)
    if User.objects.filter(pk=reqUser.pk, groups__name='themelight').exists():
        theme = 'themelight'
    else:
        theme = 'themedark'
    response = StreamingHttpResponse(LoadF5LBConfigListsOptions(deviceList, reqUser.username, theme, creds, creds2), content_type='text/html')
    response['X-Accel-Buffering'] = 'no'  # Disable buffering in nginx
    response['Cache-Control'] = 'no-cache'  # Ensure clients don't cache the data
    response['Transfer-Encoding'] = 'chunked'
    return response

@login_required(login_url='/accounts/login/')
def f5lb_get_config_options(request, device_id):
    try:
        config = F5LBConfigOptions.objects.get(device__id=device_id)
        vs_options = json.loads(config.virtual_servers or "[]")
        ssl_options = json.loads(config.ssl_policies or "[]")
        return JsonResponse({
            "virtual_servers": vs_options,
            "ssl_policies": ssl_options
        })
    except F5LBConfigOptions.DoesNotExist:
        return JsonResponse({
            "virtual_servers": [],
            "ssl_policies": []
        })