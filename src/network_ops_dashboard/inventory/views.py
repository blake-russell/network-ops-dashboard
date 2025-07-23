from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, authenticate, get_user_model, update_session_auth_hash
from django.db.models import Q
import logging
from network_ops_dashboard import settings
from network_ops_dashboard.decorators import *
from network_ops_dashboard.models import *
from network_ops_dashboard.inventory.models import *
from network_ops_dashboard.inventory.forms import *


logger = logging.getLogger('network_ops_dashboard.inventory')

# Create your views here.

@login_required(login_url='/accounts/login/')
def inventory_home(request):
    inventory_all = Inventory.objects.all().order_by('name')
    detaillist = []
    for inv in inventory_all:
        detaildict = {
            'pk' : inv.pk,
            'name' : inv.name,
            'site' : inv.site,
            'platform' : inv.platform,
			'serial_number' : inv.serial_number,
            'ipaddress_mgmt' : inv.ipaddress_mgmt,
            'device_tag' : inv.device_tag
            }
        detaillist.append(detaildict)
    return render(request, 'network_ops_dashboard/inventory/home.html', {'detaillist': detaillist})

@login_required(login_url='/accounts/login/')
def inventory_edit(request, pk):
    inv = get_object_or_404(Inventory, pk=pk)
    if request.method == 'POST':
        form = InventoryForm(request.POST, instance=inv)
        if form.is_valid():
            invform = form.save(commit=True)
            invform.save()
            return redirect('inventory_home')
    else:
        form = InventoryForm(instance=inv)
    return render(request, 'network_ops_dashboard/inventory/edit.html', {'form': form})

@login_required(login_url='/accounts/login/')
def inventory_add(request):
    if request.method == 'POST':
        form = InventoryForm(request.POST)
        if form.is_valid():
            invadd = form.save(commit=True)
            invadd.save()
            return redirect('inventory_home')
    else:
        form = InventoryForm()
    return render(request, 'network_ops_dashboard/inventory/add.html', {'form': form})

@login_required(login_url='/accounts/login/')
def platform_home(request):
    platform_all = Platform.objects.all().order_by('name')
    detaillist = []
    for platform in platform_all:
        detaildict = {
            'pk' : platform.pk,
            'manufacturer' : platform.manufacturer,
            'name' : platform.name,
            'pid' : platform.PID,
            'ansible_namespace' : platform.ansible_namespace,
            'netmiko_namespace' : platform.netmiko_namespace,
            }
        detaillist.append(detaildict)
    return render(request, 'network_ops_dashboard/inventory/platform/home.html', {'detaillist': detaillist})

@login_required(login_url='/accounts/login/')
def platform_edit(request, pk):
    plat = get_object_or_404(Platform, pk=pk)
    if request.method == 'POST':
        form = PlatformForm(request.POST, instance=plat)
        if form.is_valid():
            platform = form.save(commit=True)
            platform.save()
            return redirect('platform_home')
    else:
        form = PlatformForm(instance=plat)
    return render(request, 'network_ops_dashboard/inventory/platform/edit.html', {'form': form})

@login_required(login_url='/accounts/login/')
def platform_add(request):
    if request.method == 'POST':
        form = PlatformForm(request.POST)
        if form.is_valid():
            platadd = form.save(commit=False)
            platadd.save()
            return redirect('platform_home')
    else:
        form = PlatformForm()
    return render(request, 'network_ops_dashboard/inventory/platform/add.html', {'form': form})

@login_required(login_url='/accounts/login/')
def site_home(request):
    site_all = Site.objects.all().order_by('name')
    detaillist = []
    for site in site_all:
        detaildict = {
            'pk' : site.pk,
            'name' : site.name,
            'address' : site.address,
            'city' : site.city,
            'zip' : site.zip,
            'state' : site.state,
            'poc_name' : site.poc_name,
            'poc_number' : site.poc_number,
            }
        detaillist.append(detaildict)
    return render(request, 'network_ops_dashboard/inventory/site/home.html', {'detaillist': detaillist})

@login_required(login_url='/accounts/login/')
def site_edit(request, pk):
    site = get_object_or_404(Site, pk=pk)
    if request.method == 'POST':
        form = SiteForm(request.POST, instance=site)
        if form.is_valid():
            siteform = form.save(commit=True)
            siteform.save()
            return redirect('site_home')
    else:
        form = SiteForm(instance=site)
    return render(request, 'network_ops_dashboard/inventory/site/edit.html', {'form': form})

@login_required(login_url='/accounts/login/')
def site_add(request):
    if request.method == 'POST':
        form = SiteForm(request.POST)
        if form.is_valid():
            siteadd = form.save(commit=False)
            siteadd.save()
            return redirect('site_home')
    else:
        form = SiteForm()
    return render(request, 'network_ops_dashboard/inventory/site/add.html', {'form': form})

@login_required(login_url='/accounts/login/')
def devicetag_home(request):
    devicetag_all = DeviceTag.objects.all().order_by('name')
    detaillist = []
    for tag in devicetag_all:
        detaildict = {
            'pk' : tag.pk,
            'name' : tag.name,
            }
        detaillist.append(detaildict)
    return render(request, 'network_ops_dashboard/inventory/devicetag/home.html', {'detaillist': detaillist})

@login_required(login_url='/accounts/login/')
def devicetag_add(request):
    if request.method == 'POST':
        form = DeviceTagForm(request.POST)
        if form.is_valid():
            devicetagadd = form.save(commit=False)
            devicetagadd.save()
            return redirect('devicetag_home')
    else:
        form = DeviceTagForm()
    return render(request, 'network_ops_dashboard/inventory/devicetag/add.html', {'form': form})