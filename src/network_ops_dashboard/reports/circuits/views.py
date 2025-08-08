from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect
from django.db.models import Q
import logging
from network_ops_dashboard.decorators import *
from network_ops_dashboard.reports.circuits.models import *
from network_ops_dashboard.reports.circuits.forms import *
from network_ops_dashboard.reports.circuits.scripts.processmtcemails import *

logger = logging.getLogger('network_ops_dashboard.circuits')

# Create your views here.

@login_required(login_url='/accounts/login/')
def circuitsmtc(request):
    circuits_exist = Circuit.objects.first()
    circuitmtcemails = (
        CircuitMtcEmail.objects.filter(Q(status='Planned') | Q(status='Completed') | Q(status='Cancelled') | Q(status='Updated') | Q(status='Demand') | Q(status='Emergency'))
        .order_by('startdatetime')
        .prefetch_related('circuits__provider')
    )
    providers_with_emails = []
    for provider in CircuitProvider.objects.all():
        emails_qs = circuitmtcemails.filter(circuits__provider=provider).distinct()
        if emails_qs.exists():
            providers_with_emails.append((provider, emails_qs))
    context = {
        'circuits_exist': circuits_exist,
        'providers_with_emails': providers_with_emails,
    }
    return render(request, 'network_ops_dashboard/reports/circuits/home.html', context)

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
    circuit_all = Circuit.objects.all().order_by('name')
    detaillist = []
    for circuit in circuit_all:
        detaildict = {
            'pk' : circuit.pk,
            'name' : circuit.name,
            'cktid' : circuit.cktid,
            'provider' : circuit.provider,
            'site' : circuit.site,
            'tag' : circuit.tag,
            'notes': circuit.notes,
        }
        detaillist.append(detaildict)
    return render(request, 'network_ops_dashboard/reports/circuits/circuit.html', {'detaillist': detaillist})

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