from django.shortcuts import render, get_object_or_404, redirect
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect, JsonResponse
from django.urls import reverse
from django.db.models import Q
import logging
from network_ops_dashboard.decorators import *
from network_ops_dashboard.models import SiteSecrets, FeatureFlags
from network_ops_dashboard.notices.ciscoadvisory.forms import CiscoAdvisoryStatusForm
from network_ops_dashboard.notices.ciscoadvisory.models import CiscoAdvisory
from network_ops_dashboard.notices.ciscoadvisory.scripts.processciscoadvisoryemail import ProcessCiscoAdvisoryEmails

logger = logging.getLogger('network_ops_dashboard.ciscoadvisory')

# Create your views here.

@login_required(login_url='/accounts/login/')
def ciscoadvisory(request):
	site_secrets = SiteSecrets.objects.filter(varname='ciscoadvisory_folder')
	advisories = CiscoAdvisory.objects.filter(~Q(status='Archived')).order_by('date')
	flags = FeatureFlags.load()
	return render(request, 'network_ops_dashboard/notices/ciscoadvisory/home.html', {'advisories': advisories, 'site_secrets': site_secrets, 'feature_flags': flags})

@login_required(login_url='/accounts/login/')
def ciscoadvisory_update(request):
	ProcessCiscoAdvisoryEmails()
	return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))

@login_required(login_url='/accounts/login/')
def ciscoadvisory_assign(request, pk):
	advisory = get_object_or_404(CiscoAdvisory, pk=pk)
	advisory.status = 'Assigned'
	advisory.owner = request.user
	advisory.save()
	return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))

@login_required(login_url='/accounts/login/')
def ciscoadvisory_archive(request, pk):
	CiscoAdvisory.objects.filter(pk=pk).update(status='Archived')
	return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))

@login_required(login_url='/accounts/login/')
@require_POST
def ciscoadvisory_update_status(request, pk):
    adv = get_object_or_404(CiscoAdvisory, pk=pk)

    form = CiscoAdvisoryStatusForm(request.POST)
    if not form.is_valid():
        return JsonResponse({"ok": False, "errors": form.errors}, status=400)

    adv.status = form.cleaned_data["status"]
    adv.note = form.cleaned_data["note"]
    adv.save(update_fields=["status", "note"])

    if request.headers.get("HX-Request"):
        return HttpResponse(status=204, headers={"HX-Redirect": reverse("ciscoadvisory")})
    return redirect("ciscoadvisory")