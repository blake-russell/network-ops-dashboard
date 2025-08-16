from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.http import JsonResponse
from django.db.models import Q
import logging
from network_ops_dashboard.decorators import *
from network_ops_dashboard.models import *
from network_ops_dashboard.sitesettings.forms import *


logger = logging.getLogger('network_ops_dashboard.sitesettings')

# Create your views here.

@staff_member_required
def sitesettings_edit(request):
    obj, _ = SiteSettings.objects.get_or_create(
        pk=1,
        defaults={"company": "Company Name", "teamname": "Team Name"},
    )
    if request.method == "POST":
        form = SiteSettingsForm(request.POST, instance=obj)
        if form.is_valid():
            form.save()
            return redirect("dashboard")
    else:
        form = SiteSettingsForm(instance=obj)
    return render(request, "network_ops_dashboard/sitesettings/sitesettings_edit.html", {"form": form})

@staff_member_required
def websites_home(request):
    websites_all = SiteSettingsWebsite.objects.all().order_by('name')
    detaillist = []
    for website in websites_all:
        detaildict = {
            'pk' : website.pk,
            'name' : website.name,
            'url' : website.url,
            }
        detaillist.append(detaildict)
    return render(request, 'network_ops_dashboard/sitesettings/sitesettingswebsites_home.html', {'detaillist': detaillist})

@staff_member_required
def websites_edit(request, pk):
    site = get_object_or_404(SiteSettingsWebsite, pk=pk)
    if request.method == 'POST':
        form = SiteSettingsWebsiteForm(request.POST, instance=site)
        if form.is_valid():
            website = form.save(commit=True)
            website.save()
            return redirect('websites_home')
    else:
        form = SiteSettingsWebsiteForm(instance=site)
    return render(request, 'network_ops_dashboard/sitesettings/sitesettingswebsites_edit.html', {'form': form})

@staff_member_required
def websites_add(request):
    if request.method == 'POST':
        form = SiteSettingsWebsiteForm(request.POST)
        if form.is_valid():
            website = form.save(commit=False)
            website.save()
            return redirect('websites_home')
    else:
        form = SiteSettingsWebsiteForm()
    return render(request, 'network_ops_dashboard/sitesettings/sitesettingswebsites_add.html', {'form': form})

@login_required(login_url='/accounts/login/')
def secrets_home(request):
    secrets_all = SiteSecrets.objects.all().order_by('varname')
    detaillist = []
    for secret in secrets_all:
        detaildict = {
            'pk' : secret.pk,
            'varname' : secret.varname,
            'varvalue' : secret.varvalue,
            }
        detaillist.append(detaildict)
    return render(request, 'network_ops_dashboard/sitesettings/sitesecrets_home.html', {'detaillist': detaillist})

@login_required(login_url='/accounts/login/')
def secrets_edit(request, pk):
    secret = get_object_or_404(SiteSecrets, pk=pk)
    if request.method == 'POST':
        form = SiteSecretsForm(request.POST, instance=secret)
        if form.is_valid():
            secret_form = form.save(commit=True)
            secret_form.save()
            return redirect('secrets_home')
    else:
        form = SiteSecretsForm(instance=secret)
    return render(request, 'network_ops_dashboard/sitesettings/sitesecrets_edit.html', {'form': form})

@login_required(login_url='/accounts/login/')
def secrets_add(request):
    if request.method == 'POST':
        form = SiteSecretsForm(request.POST)
        if form.is_valid():
            secret = form.save(commit=False)
            secret.save()
            return redirect('secrets_home')
    else:
        form = SiteSecretsForm()
    return render(request, 'network_ops_dashboard/sitesettings/sitesecrets_add.html', {'form': form})