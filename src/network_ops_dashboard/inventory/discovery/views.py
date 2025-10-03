from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from network_ops_dashboard.inventory.discovery.scripts.services import run_discovery
from network_ops_dashboard.inventory.discovery.forms import DiscoveryForm
from network_ops_dashboard.inventory.models import Inventory, InventoryInterface, Platform, Site
from network_ops_dashboard.inventory.discovery.models import DiscoveryJob, DiscoveredDevice
from network_ops_dashboard.inventory.discovery.tasks import start_discovery_in_thread

@require_POST
@login_required(login_url='/accounts/login/')
def inventory_discovery_start(request):  
    form = DiscoveryForm(request.POST)
    if not form.is_valid():
        return render(request, "network_ops_dashboard/inventory/home.html", {"discovery_form": form, "discovery_form_errors": form.errors}, status=400)

    data = form.cleaned_data.copy()
    cred = data.get('credential')
    if cred is not None:
        data['credential'] = cred.pk

    job = DiscoveryJob.objects.create(
        created_by=request.user,
        params=data,
        status=DiscoveryJob.Status.PENDING,
    )
    # Spin up background thread
    start_discovery_in_thread(job.id)

    return redirect("inventory_discovery_results", job_id=str(job.id))

@login_required(login_url='/accounts/login/')
def inventory_discovery_results(request, job_id):
    job = get_object_or_404(DiscoveryJob, pk=job_id)
    devices = job.devices.order_by("ip")
    sites = Site.objects.order_by("name")
    return render(request, "network_ops_dashboard/inventory/discovery/results.html", {"job": job, "devices": devices, "sites": sites})

@require_POST
@login_required(login_url='/accounts/login/')
def inventory_discovery_install(request, device_id):
    d = get_object_or_404(DiscoveredDevice, pk=device_id)

    # Get overrides from form
    hostname = request.POST.get("hostname") or d.hostname or d.ip
    vendor = d.raw.get("vendor", "")
    model = request.POST.get("model") or d.raw.get("model", "")
    pid = request.POST.get("pid") or d.platform_guess or ""
    version = d.raw.get("version", "")
    serial = d.raw.get("serial", "")
    site_id = request.POST.get("site")
    site_obj = get_object_or_404(Site, pk=site_id)

    # Find or create Platform entry
    platform_obj, _ = Platform.objects.get_or_create(
        manufacturer=vendor,
        PID=pid,
        name=model,
    )

    # Create Inventory device
    new_dev = Inventory.objects.create(
        name=hostname,
        name_lookup=hostname,
        ipaddress_mgmt=d.ip,
        serial_number=serial,
        platform=platform_obj,
        first_seen_at=timezone.now(),
        discovery_source=d.discovered_via,
        sw_version=version,
        site=site_obj,
    )

    for iface in d.raw.get("interfaces", []):
        InventoryInterface.objects.create(device=new_dev, name=iface)

    d.added_to_inventory = True
    d.save()

    return redirect("inventory_home")

@login_required(login_url='/accounts/login/')
def inventory_discovery_status(request, job_id):
    job = get_object_or_404(DiscoveryJob, pk=job_id)
    devices = job.devices.order_by("ip")
    sites = Site.objects.all()
    return render(request, "network_ops_dashboard/inventory/discovery/_status.html", {"job": job, "devices": devices, "sites": sites})