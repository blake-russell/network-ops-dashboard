from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, authenticate, get_user_model, update_session_auth_hash
from django.http import HttpResponseRedirect
from django.db.models import Q
#from django_xhtml2pdf.utils import generate_pdf, pdf_decorator
import logging
from network_ops_dashboard import settings
from network_ops_dashboard.decorators import *
from network_ops_dashboard.models import *
from network_ops_dashboard.notices.certexpiry.forms import *
from network_ops_dashboard.notices.certexpiry.models import *
from network_ops_dashboard.notices.certexpiry.scripts.processcertexpiryemail import *

logger = logging.getLogger('network_ops_dashboard.certexpiry')

# Create your views here.

@login_required(login_url='/accounts/login/')
def certexpiry(request):
    cert_providers = CertProvider.objects.first()
    certs = CertExpiry.objects.filter(Q(status='Open')).order_by('expire_date')
    return render(request, 'network_ops_dashboard/notices/certexpiry/home.html', {'certs': certs, 'cert_providers': cert_providers })

@login_required(login_url='/accounts/login/')
def certexpiry_update(request):
	ProcessCertExpiryEmails()
	return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))

@login_required(login_url='/accounts/login/')
def certexpiry_archive(request, pk):
	CertExpiry.objects.filter(pk=pk).update(status='Closed')
	return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))

@login_required(login_url='/accounts/login/')
def certexpiry_provider(request):
    cert_providers = CertProvider.objects.all()
    return render(request, 'network_ops_dashboard/notices/certexpiry/certexpiry_provider.html', {'cert_providers': cert_providers })

@login_required(login_url='/accounts/login/')
def certexpiry_provider_edit(request, pk):
    provider = get_object_or_404(CertProvider, pk=pk)
    if request.method == 'POST':
        form = CertProviderForm(request.POST, instance=provider)
        if form.is_valid():
            provider_add = form.save(commit=True)
            provider_add.save()
            return redirect('certexpiry_provider')
    else:
        form = CertProviderForm(instance=provider)
    return render(request, 'network_ops_dashboard/notices/certexpiry/certexpiry_provider_edit.html', {'form': form})

@login_required(login_url='/accounts/login/')
def certexpiry_provider_add(request):
    if request.method == 'POST':
        form = CertProviderForm(request.POST)
        if form.is_valid():
            provider_add = form.save(commit=False)
            provider_add.save()
            return redirect('certexpiry_provider')
    else:
        form = CertProviderForm()
    return render(request, 'network_ops_dashboard/notices/certexpiry/certexpiry_provider_add.html', {'form': form})