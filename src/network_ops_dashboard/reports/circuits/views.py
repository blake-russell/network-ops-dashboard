from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponseForbidden, HttpResponseRedirect
from django.db.models import Q
import logging
from network_ops_dashboard.decorators import *
from network_ops_dashboard.models import FeatureFlags
from network_ops_dashboard.reports.circuits.models import *
from network_ops_dashboard.reports.circuits.forms import *
from network_ops_dashboard.reports.circuits.scripts.processmtcemails import *

logger = logging.getLogger('network_ops_dashboard.circuits')

def _user_can_archive(user, email_obj: CircuitMtcEmail) -> bool:
    if user.is_superuser or user.is_staff:
        return True
    user_groups = set(user.groups.values_list('name', flat=True))
    tag_names = set(email_obj.circuits.values_list('tag__name', flat=True))
    return bool(user_groups & tag_names)
    
# Create your views here.

@login_required(login_url='/accounts/login/')
def circuitsmtc(request):
    status_choices = (CircuitMtcEmail.objects
                      .values_list('status', flat=True)
                      .distinct().order_by('status'))
    tag_choices = (CircuitTag.objects
                   .values_list('name', flat=True)
                   .distinct().order_by('name'))
    flags = FeatureFlags.load()
    return render(request, 'network_ops_dashboard/reports/circuits/home.html', {
        'circuits_exist': Circuit.objects.first(),
        'feature_flags': flags,
        'status_choices': status_choices,
        'tag_choices': tag_choices,
    })

@login_required(login_url='/accounts/login/')
def circuitsmtc_data(request):
    q = (request.GET.get('q') or '').strip()

    def _get_multi(param):
        vals = request.GET.getlist(param)
        if not vals and request.GET.get(param):
            vals = [v.strip() for v in request.GET.get(param).split(',')]
        return [v for v in (vals or []) if v]

    statuses = _get_multi('status')
    tags = _get_multi('tag')

    base = (CircuitMtcEmail.objects
            .filter(status__in=['Planned','Completed','Cancelled','Updated','Demand','Emergency'])
            .select_related()
            .prefetch_related('circuits__provider', 'circuits__tag'))

    if statuses:
        base = base.filter(status__in=statuses)

    if tags:
        base = base.filter(circuits__tag__name__in=tags)

    if q:
        base = base.filter(
            Q(circuits__name__icontains=q) |
            Q(mtc_id__icontains=q)
        )

    base = base.distinct()

    rows = []

    for e in base:
        providers = sorted({c.provider.name for c in e.circuits.all() if c.provider})
        circuits = sorted({c.name for c in e.circuits.all()})
        circuit_ids = sorted({c.cktid for c in e.circuits.all() if getattr(c, 'cktid', None)})
        tag_names = sorted({t.name for c in e.circuits.all() for t in c.tag.all()})
        rows.append({
            "pk": e.pk,
            "providers": providers,
            "provider": providers[0] if providers else "",
            "name_list": circuits,
            "name": circuits[0] if circuits else "",
            "cktid_list": circuit_ids,
            "mtc_id": e.mtc_id,
            "status": e.status or "",
            "impact": e.impact or "",
            "startdatetime": str(e.startdatetime) if e.startdatetime else "",
            "enddatetime": str(e.enddatetime) if e.enddatetime else "",
            "tags": tag_names,
            "can_archive": _user_can_archive(request.user, e),
        })
    return JsonResponse({"rows": rows})

@login_required(login_url='/accounts/login/')
def circuitsmtc_update(request):
    circuit_id_list = Circuit.objects.all()
    ProcessCircuitMtcEmails(circuit_id_list)
    return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))

@login_required(login_url='/accounts/login/')
def circuitsmtc_archive(request, pk):
    CircuitMtcEmail.objects.filter(pk=pk).update(status='Archived')
    return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))

@login_required(login_url='/accounts/login/')
def circuittag(request):
    circuittag_all = CircuitTag.objects.all().order_by('name')
    detaillist = []
    for circuittag in circuittag_all:
        detaildict = {
            'pk' : circuittag.pk,
            'name' : circuittag.name,
        }
        detaillist.append(detaildict)
    return render(request, 'network_ops_dashboard/reports/circuits/circuittag.html', {'detaillist': detaillist})

@login_required(login_url='/accounts/login/')
def circuittag_add(request):
    if request.method == 'POST':
        form = CircuitTagForm(request.POST)
        if form.is_valid():
            circuittag = form.save(commit=False)
            circuittag.save()
            return redirect('circuittag')
    else:
        form = CircuitTagForm()
    return render(request, 'network_ops_dashboard/reports/circuits/circuittag_add.html', {'form': form})

@login_required(login_url='/accounts/login/')
def circuitprovider(request):
    circuitprovider_all = CircuitProvider.objects.all().order_by('name')
    detaillist = []
    for circuitprovider in circuitprovider_all:
        detaildict = {
            'pk' : circuitprovider.pk,
            'name' : circuitprovider.name,
            'email_folder' : circuitprovider.email_folder,
            'function_name' : circuitprovider.function_name,
        }
        detaillist.append(detaildict)
    return render(request, 'network_ops_dashboard/reports/circuits/circuitprovider.html', {'detaillist': detaillist})

@login_required(login_url='/accounts/login/')
def circuitprovider_edit(request, pk):
    provider = get_object_or_404(CircuitProvider, pk=pk)
    if request.method == 'POST':
        form = CircuitProviderForm(request.POST, instance=provider)
        if form.is_valid():
            circuitprovider = form.save(commit=True)
            circuitprovider.save()
            return redirect('circuitprovider')
    else:
        form = CircuitProviderForm(instance=provider)
    return render(request, 'network_ops_dashboard/reports/circuits/circuitprovider_edit.html', {'form': form})

@login_required(login_url='/accounts/login/')
def circuitprovider_add(request):
    if request.method == 'POST':
        form = CircuitProviderForm(request.POST)
        if form.is_valid():
            circuitprovider = form.save(commit=False)
            circuitprovider.save()
            return redirect('circuitprovider')
    else:
        form = CircuitProviderForm()
    return render(request, 'network_ops_dashboard/reports/circuits/circuitprovider_add.html', {'form': form})

@login_required(login_url='/accounts/login/')
def circuit(request):
    provider_choices = (CircuitProvider.objects
                        .order_by('name')
                        .values_list('name', flat=True)
                        .distinct())
    site_choices = (Site.objects
                    .order_by('name')
                    .values_list('name', flat=True)
                    .distinct())
    tag_choices = (CircuitTag.objects
                   .order_by('name')
                   .values_list('name', flat=True)
                   .distinct())

    return render(request, 'network_ops_dashboard/reports/circuits/circuit.html', {
        'provider_choices': provider_choices,
        'site_choices': site_choices,
        'tag_choices': tag_choices,
    })

@login_required(login_url='/accounts/login/')
def circuit_data(request):
    def _get_multi(param):
        vals = request.GET.getlist(param)
        if not vals and request.GET.get(param):
            vals = [v.strip() for v in request.GET.get(param).split(',')]
        return [v for v in (vals or []) if v]

    providers = _get_multi('provider')
    sites = _get_multi('site')
    tags = _get_multi('tag')
    q = (request.GET.get('q') or '').strip()

    qs = (Circuit.objects
          .select_related('provider', 'site')
          .prefetch_related('tag')
          .all())

    if providers:
        qs = qs.filter(provider__name__in=providers)
    if sites:
        qs = qs.filter(site__name__in=sites)
    if tags:
        qs = qs.filter(tag__name__in=tags)

    if q:
        qs = qs.filter(
            Q(name__icontains=q) |
            Q(cktid__icontains=q) |
            Q(provider__name__icontains=q) |
            Q(site__name__icontains=q) |
            Q(tag__name__icontains=q)
        ).distinct()

    rows = []
    for c in qs:
        rows.append({
            "pk": c.pk,
            "name": c.name or "",
            "cktid": c.cktid or "",
            "provider": c.provider.name if c.provider else "",
            "site": c.site.name if c.site else "",
            "site_full": (
                f"{c.site.address}, {c.site.city}, {c.site.state} {c.site.zip}"
                if c.site else ""
            ),
            "tags": [t.name for t in c.tag.all()],
        })
    return JsonResponse({"rows": rows})

@login_required(login_url='/accounts/login/')
def circuit_edit(request, pk):
    circuits = get_object_or_404(Circuit, pk=pk)
    if request.method == 'POST':
        form = CircuitForm(request.POST, instance=circuits)
        if form.is_valid():
            circuit = form.save(commit=True)
            circuit.save()
            return redirect('circuit')
    else:
        form = CircuitForm(instance=circuits)
    return render(request, 'network_ops_dashboard/reports/circuits/circuit_edit.html', {'form': form})

@login_required(login_url='/accounts/login/')
def circuit_add(request):
    if request.method == 'POST':
        form = CircuitForm(request.POST)
        if form.is_valid():
            circuit = form.save(commit=False)
            circuit.save()
            form.save_m2m()
            return redirect('circuit')
    else:
        form = CircuitForm()
    return render(request, 'network_ops_dashboard/reports/circuits/circuit_add.html', {'form': form})