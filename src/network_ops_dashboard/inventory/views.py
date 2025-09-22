from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.db.models import Q
import logging
from network_ops_dashboard.decorators import *
from network_ops_dashboard.models import *
from network_ops_dashboard.inventory.models import Inventory, Site, Platform, DeviceTag
from network_ops_dashboard.inventory.discovery.forms import DiscoveryForm
from network_ops_dashboard.inventory.forms import *


logger = logging.getLogger('network_ops_dashboard.inventory')

# Create your views here.

@login_required(login_url='/accounts/login/')
def inventory_home(request):
    site_choices = Site.objects.order_by('name').values_list('name', flat=True).distinct()
    platform_choices = Platform.objects.order_by('name').values_list('name', flat=True).distinct()
    tag_choices = DeviceTag.objects.order_by('name').values_list('name', flat=True)
    discovery_form = DiscoveryForm()

    return render(request, "network_ops_dashboard/inventory/home.html", {
        "site_choices": site_choices,
        "platform_choices": platform_choices,
        "tag_choices": tag_choices,
        "discovery_form": discovery_form,
    })

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
    name_choices = (Site.objects
                    .exclude(name__isnull=True)
                    .exclude(name__exact="")
                    .order_by('name')
                    .values_list('name', flat=True)
                    .distinct())
    city_choices = (Site.objects
                    .exclude(city__isnull=True)
                    .exclude(city__exact="")
                    .order_by('city')
                    .values_list('city', flat=True)
                    .distinct())
    state_choices = (Site.objects
                     .exclude(state__isnull=True)
                     .exclude(state__exact="")
                     .order_by('state')
                     .values_list('state', flat=True)
                     .distinct())

    return render(request, "network_ops_dashboard/inventory/site/home.html", {
        "name_choices": name_choices,
        "city_choices": city_choices,
        "state_choices": state_choices,
    })

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

@login_required(login_url='/accounts/login/')
def inventory_data(request):
    site = request.GET.get('site', '').strip()
    platform = request.GET.get('platform', '').strip()
    tag = request.GET.get('tag', '').strip()
    q = request.GET.get('q', '').strip()

    qs = (Inventory.objects
          .select_related('site', 'platform')
          .prefetch_related('device_tag')
          .all())
    
    if site:
        qs = qs.filter(site__name__icontains=site)
    if platform:
        qs = qs.filter(platform__name__icontains=platform)
    if tag:
        qs = qs.filter(device_tag__name__iexact=tag)
    if q:
        qs = qs.filter(
            Q(name__icontains=q) |
            Q(serial_number__icontains=q) |
            Q(ipaddress_mgmt__icontains=q)
        ).distinct()

    rows = []

    for d in qs:
        rows.append({
            "pk": d.pk,
            "name": d.name,
            "site": d.site.name if d.site else "",
            "platform": d.platform.name if d.platform else "",
            "serial_number": d.serial_number or "",
            "ipaddress_mgmt": d.ipaddress_mgmt or "",
            "tags": [t.name for t in d.device_tag.all()],
        })
    return JsonResponse({"rows": rows})

@login_required(login_url='/accounts/login/')
def site_data(request):
    name  = request.GET.get('name', '').strip()
    city  = request.GET.get('city', '').strip()
    state = request.GET.get('state', '').strip()
    q     = request.GET.get('q', '').strip()

    qs = Site.objects.all()

    if name:
        qs = qs.filter(name__icontains=name)
    if city:
        qs = qs.filter(city__icontains=city)
    if state:
        qs = qs.filter(state__iexact=state)
    if q:
        qs = qs.filter(
            Q(name__icontains=q) |
            Q(address__icontains=q) |
            Q(city__icontains=q) |
            Q(state__icontains=q) |
            Q(zip__icontains=q) |
            Q(poc_name__icontains=q) |
            Q(poc_number__icontains=q)
        ).distinct()

    rows = []

    for s in qs:
        rows.append({
            "pk": s.pk,
            "name": s.name or "",
            "address": s.address or "",
            "city": s.city or "",
            "state": s.state or "",
            "zip": s.zip or "",
            "poc_name": s.poc_name or "",
            "poc_number": s.poc_number or "",
        })
    return JsonResponse({"rows": rows})

@login_required(login_url='/accounts/login/')
def networkcreds_home(request):
    networkcreds_all = NetworkCredential.objects.all().order_by('username_search_field')
    detaillist = []
    for networkcreds in networkcreds_all:
        detaildict = {
            'pk' : networkcreds.pk,
            'username' : networkcreds.username,
            'username_search_field' : networkcreds.username_search_field,
            }
        detaillist.append(detaildict)
    return render(request, 'network_ops_dashboard/inventory/networkcreds/home.html', {'detaillist': detaillist})

@login_required(login_url='/accounts/login/')
def networkcreds_edit(request, pk):
    networkcred = get_object_or_404(NetworkCredential, pk=pk)
    if request.method == 'POST':
        form = NetworkCredentialForm(request.POST, instance=networkcred)
        if form.is_valid():
            cred = form.save(commit=True)
            cred.save()
            return redirect('networkcreds_home')
    else:
        form = NetworkCredentialForm(instance=networkcred)
    return render(request, 'network_ops_dashboard/inventory/networkcreds/edit.html', {'form': form})

@login_required(login_url='/accounts/login/')
def networkcreds_add(request):
    if request.method == 'POST':
        form = NetworkCredentialForm(request.POST)
        if form.is_valid():
            cred = form.save(commit=False)
            cred.save()
            return redirect('networkcreds_home')
    else:
        form = NetworkCredentialForm()
    return render(request, 'network_ops_dashboard/inventory/networkcreds/add.html', {'form': form})