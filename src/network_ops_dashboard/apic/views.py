from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, authenticate, get_user_model, update_session_auth_hash
from django.http import HttpResponseRedirect, StreamingHttpResponse, JsonResponse
from django.db.models import Q
import logging
import json
from network_ops_dashboard import settings
from network_ops_dashboard.decorators import *
from network_ops_dashboard.models import *
from network_ops_dashboard.inventory.models import *
from network_ops_dashboard.apic.models import *
from network_ops_dashboard.apic.forms import *
from network_ops_dashboard.apic.scripts.createinterface import APICMopCreateInterfaceRun
from network_ops_dashboard.apic.scripts.loadconfiglistoptions import LoadAPICConfigListOptions


logger = logging.getLogger('network_ops_dashboard.apic')

# Create your views here.

@login_required(login_url='/accounts/login/')
def apic_createinterface(request):
    # SiteSecrets.objects() check
    secret_search = ['apic_primary_user', 'apic_secondary_user', 'backLink_apic_createinterface', 'apic_lab_device_1', 'apic_lab_device_2']
    site_secret = SiteSecrets.objects.filter(varname__in=secret_search)
    site_secrets = {s.varname: s.varvalue for s in site_secret}
    for key in secret_search:
        site_secrets.setdefault(key, None)
    missing_keys = [key for key in secret_search if site_secrets[key] is None]
    # Instead of sending entire objects.all do filtering here in view then display entire dict in template.
    if request.user.groups.filter(name='site-admin').exists():
        apic_mops_all = APICMopCreateInterface.objects.filter(Q(status='Planned') | Q(status='Completed') | Q(status='Cancelled') | Q(status='Running')).order_by('status')
    else:
        apic_mops_all = APICMopCreateInterface.objects.filter(Q(status='Planned') | Q(status='Completed') | Q(status='Cancelled') | Q(status='Running'), Q(user=request.user)).order_by('status')
    detaillist = []
    for mop in apic_mops_all:
        detaildict = {
            'pk' : mop.pk,
            'name' : mop.name,
            'status' : mop.status,
            'device' : mop.device,
            'interfaces' : mop.interfaces,
            }
        detaillist.append(detaildict)
    return render(request, 'network_ops_dashboard/apic/mop_createinterface.html', {'detaillist': detaillist, 'site_secrets': site_secrets, 'missing_keys': missing_keys })

@login_required(login_url='/accounts/login/')
def apic_createinterface_edit(request, pk):
    apic_mop = get_object_or_404(APICMopCreateInterface, pk=pk)
    if request.method == 'POST':
        form = APICMopCreateInterfaceEditForm(request.POST, user=request.user, instance=apic_mop)
        if form.is_valid():
            apic_mop = form.save(commit=True)
            apic_mop.save()
            return redirect('apic_createinterface')
    else:
        form = APICMopCreateInterfaceEditForm(instance=apic_mop, user=request.user)
    return render(request, 'network_ops_dashboard/apic/mop_createinterface_edit.html', {'form': form})

@login_required(login_url='/accounts/login/')
def apic_createinterface_add(request):
    if request.method == 'POST':
        form = APICMopCreateInterfaceAddForm(request.POST)
        if form.is_valid():
            apic_mop = form.save(commit=False)
            apic_mop.user = request.user
            apic_mop.save()
            return redirect('apic_createinterface')
    else:
        form = APICMopCreateInterfaceAddForm()
    return render(request, 'network_ops_dashboard/apic/mop_createinterface_add.html', {'form': form})

@login_required(login_url='/accounts/login/')
def apic_createinterface_archive(request, pk):
    mop_entry = get_object_or_404(APICMopCreateInterface, pk=pk)
    mop_entry.interfaces.all().delete()
    mop_entry.status = 'Closed'
    mop_entry.save()
    return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))

@login_required(login_url='/accounts/login/')
def apic_createinterface_intf(request):
    # Instead of sending entire objects.all do filtering here in view then display entire dict in template.
    if request.user.groups.filter(name='site-admin').exists():
        apic_intf_all = APICMopInterface.objects.all()
    else:
        apic_intf_all = APICMopInterface.objects.filter(Q(user=request.user)).order_by('intfdesc')
    detaillist = []
    for intf in apic_intf_all:
        detaildict = {
            'pk' : intf.pk,
            'intfdesc' : intf.intfdesc,
            'intfprofile' : intf.intfprofile,
            'intfselector' : intf.intfselector,
            'intfipg' : intf.intfipg,
            'intffromport' : intf.intffromport,
            'intftoport' : intf.intftoport,
            }
        detaillist.append(detaildict)
    return render(request, 'network_ops_dashboard/apic/mop_createinterface_intf.html', {'detaillist': detaillist})

@login_required(login_url='/accounts/login/')
def apic_createinterface_addintf(request, pk):
    apic_mop = get_object_or_404(APICMopCreateInterface, pk=pk)
    if request.method == 'POST':
        form = APICMopInterfaceForm(request.POST)
        if form.is_valid():
            apic_intf = form.save(commit=False)
            apic_intf.user = request.user
            apic_intf.save()
            apic_mop.interfaces.add(apic_intf)
            return redirect('apic_createinterface')
    else:
        # SiteSecrets.objects() check
        secret_search = ['apic_primary_user', 'apic_secondary_user', 'backLink_apic_createinterface', 'apic_lab_device_1', 'apic_lab_device_2']
        site_secret = SiteSecrets.objects.filter(varname__in=secret_search)
        site_secrets = {s.varname: s.varvalue for s in site_secret}
        for key in secret_search:
            site_secrets.setdefault(key, None)
        missing_keys = [key for key in secret_search if site_secrets[key] is None]
        initial_data = {
            'device': apic_mop.device
        }
        form = APICMopInterfaceForm(initial=initial_data, readonly_device=True)
    return render(request, 'network_ops_dashboard/apic/mop_createinterface_addintf.html', {'form': form, 'site_secrets': site_secrets, 'missing_keys': missing_keys })

@login_required(login_url='/accounts/login/')
def apic_createinterface_editintf(request, pk):
    apic_intf = get_object_or_404(APICMopInterface, pk=pk)
    if request.method == 'POST':
        form = APICMopInterfaceForm(request.POST, instance=apic_intf)
        if form.is_valid():
            apic_intf = form.save(commit=True)
            apic_intf.save()
            return redirect('apic_createinterface_intf')
    else:
        # SiteSecrets.objects() check
        secret_search = ['apic_primary_user', 'apic_secondary_user', 'backLink_apic_createinterface', 'apic_lab_device_1', 'apic_lab_device_2']
        site_secret = SiteSecrets.objects.filter(varname__in=secret_search)
        site_secrets = {s.varname: s.varvalue for s in site_secret}
        for key in secret_search:
            site_secrets.setdefault(key, None)
        missing_keys = [key for key in secret_search if site_secrets[key] is None]
        form = APICMopInterfaceForm(instance=apic_intf, readonly_device=True)
    return render(request, 'network_ops_dashboard/apic/mop_createinterface_editintf.html', {'form': form, 'site_secrets': site_secrets, 'missing_keys': missing_keys })

@login_required(login_url='/accounts/login/')
def apic_createinterface_delintf(request, pk):
    apic_intf = get_object_or_404(APICMopInterface, pk=pk)
    apic_intf.delete()
    return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))

@login_required(login_url='/accounts/login/')
def apic_createinterface_run(request, pk):
    APICMopCreateInterface.objects.filter(pk=pk).update(status='Running')
    mop = APICMopCreateInterface.objects.filter(pk=pk)
    try:
        apic_lab_device_1 = SiteSecrets.objects.filter(varname='apic_lab_device_1')[0].varvalue
        apic_lab_device_2 = SiteSecrets.objects.filter(varname='apic_lab_device_2')[0].varvalue
        apic_primary_user = SiteSecrets.objects.filter(varname='apic_primary_user')[0].varvalue
        apic_secondary_user = SiteSecrets.objects.filter(varname='apic_secondary_user')[0].varvalue
        if mop[0].device.ipaddress_mgmt == apic_lab_device_1 or mop[0].device.ipaddress_mgmt == apic_lab_device_2:
            creds = NetworkCredential.objects.filter(username_lookup=apic_secondary_user) # Use this apic_secondary_user if LAB device
        else:
            creds = NetworkCredential.objects.filter(username_lookup=apic_primary_user) # Use apic_primary_user if production device
    except Exception as e:
        try:
            # exception here if apic_lab_device_1 and apic_lab_device_2 are not set in SiteSecrets.objects() for lab devices
            creds = NetworkCredential.objects.filter(username_lookup=apic_primary_user) # Use apic_primary_user if production device
            logger.exception('apic_createinterface_run (Exception) importing apic_lab_device_1/2 or secondary_user from SiteSecrets.objects(). %s' %(e))
        except Exception as e:
            logger.exception('apic_createinterface_run (Exception) importing apic_primary_user/secondary_user or apic_lab_device_1/2 from SiteSecrets.objects() %s' %(e))
            response = HttpResponse(f"apic_createinterface_run (Exception) importing apic_primary_user/secondary_user or apic_lab_device_1/2 from SiteSecrets.objects().: {e}", content_type='text/html')
            return response
    reqUser = User.objects.get(username=request.user)
    if User.objects.filter(pk=reqUser.pk, groups__name='themelight').exists():
        theme = 'themelight'
    else:
        theme = 'themedark'
    response = StreamingHttpResponse(APICMopCreateInterfaceRun(mop, reqUser.username, theme, creds), content_type='text/html')
    response['X-Accel-Buffering'] = 'no'  # Disable buffering in nginx
    response['Cache-Control'] = 'no-cache'  # Ensure clients don't cache the data
    response['Transfer-Encoding'] = 'chunked'
    return response

@login_required(login_url='/accounts/login/')
def apic_loadconfigoptions(request, device_id):
    if device_id == '4096':
        deviceList = APICConfigOptions.objects.all()
    else:
        deviceList = APICConfigOptions.objects.filter(device__id=device_id)
    try:
        apic_primary_user = SiteSecrets.objects.filter(varname='apic_primary_user')[0].varvalue
        apic_secondary_user = SiteSecrets.objects.filter(varname='apic_secondary_user')[0].varvalue
        creds = NetworkCredential.objects.filter(username_lookup=apic_primary_user)
        creds2 = NetworkCredential.objects.filter(username_lookup=apic_secondary_user)
    except Exception as e:
        try:
            creds = NetworkCredential.objects.filter(username_lookup=apic_primary_user)
            creds2 = NetworkCredential.objects.filter(username_lookup=apic_primary_user)
            logger.exception('apic_loadconfigoptions (Exception) importing apic_secondary_user from SiteSecrets.objects(). %s' %(e))
        except Exception as e:
            logger.exception('apic_loadconfigoptions (Exception) importing apic_primary_user from SiteSecrets.objects(). %s' %(e))
            response = HttpResponse(f"apic_loadconfigoptions (Exception) importing apic_primary_user from SiteSecrets.objects(): {e}", content_type='text/html')
            return response
    reqUser = User.objects.get(username=request.user)
    if User.objects.filter(pk=reqUser.pk, groups__name='themelight').exists():
        theme = 'themelight'
    else:
        theme = 'themedark'
    response = StreamingHttpResponse(LoadAPICConfigListOptions(deviceList, reqUser.username, theme, creds, creds2), content_type='text/html')
    response['X-Accel-Buffering'] = 'no'  # Disable buffering in nginx
    response['Cache-Control'] = 'no-cache'  # Ensure clients don't cache the data
    response['Transfer-Encoding'] = 'chunked'
    return response

@login_required(login_url='/accounts/login/')
def apic_get_config_options(request, device_id):
    try:
        config = APICConfigOptions.objects.get(device__id=device_id)
        ipf_options = json.loads(config.interface_profiles or "[]")
        ipg_options = json.loads(config.interface_policy_groups or "[]")
        return JsonResponse({
            "interface_profiles": ipf_options,
            "interface_policy_groups": ipg_options
        })
    except APICConfigOptions.DoesNotExist:
        return JsonResponse({
            "interface_profiles": [],
            "interface_policy_groups": []
        })