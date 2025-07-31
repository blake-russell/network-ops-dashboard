from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User, Group
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login, authenticate, get_user_model, update_session_auth_hash
from django.http import HttpResponseRedirect, HttpResponse
from django.db.models import Q
from django.utils import timezone
from datetime import timedelta
#from django_xhtml2pdf.utils import generate_pdf, pdf_decorator
import logging
from network_ops_dashboard import settings
from network_ops_dashboard.decorators import *
from network_ops_dashboard.models import *
from network_ops_dashboard.asavpn.models import AsaVpnConnectedUsers
from network_ops_dashboard.notices.svcactexpiry.models import SvcActExpiry
from network_ops_dashboard.notices.ciscoadvisory.models import CiscoAdvisory
from network_ops_dashboard.notices.certexpiry.models import CertExpiry
from network_ops_dashboard.forms import *

logger = logging.getLogger('network_ops_dashboard')

# Create your views here.

def home(request):
    site_settings = SiteSettings.objects.first()
    return render(request, 'network_ops_dashboard/home.html', {'site_settings': site_settings})

def signup(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get('username')
            raw_password = form.cleaned_data.get('password1')
            user = authenticate(username=username, password=raw_password)
            login(request, user)
            return redirect('dashboard')
    else:
        form = UserCreationForm()
    return render(request, 'registration/signup.html', {'form': form})

@login_required(login_url='/accounts/login/')
def change_password(request):
    return render(request, 'registration/change_password.html')

@login_required(login_url='/accounts/login/')
def change_password_done(request):
	return render(request, 'registration/change_password_done.html')

@login_required(login_url='/accounts/login/')
def themelight(request):
	user = request.user
	newtheme = Group.objects.get(name='themelight')
	oldtheme = Group.objects.get(name='themedark')
	user.groups.remove(oldtheme)
	user.groups.add(newtheme)
	return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))

@login_required(login_url='/accounts/login/')
def themedark(request):
	user = request.user
	newtheme = Group.objects.get(name='themedark')
	oldtheme = Group.objects.get(name='themelight')
	user.groups.remove(oldtheme)
	user.groups.add(newtheme)
	return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))

@login_required(login_url='/accounts/login/')
def dashboard(request):
    statusmessages = []
    if not User.objects.all():
        statusmessages.append('- No users exist. Create superuser in shell: "python manage.py createsuperuser"')
    site_settings = SiteSettings.objects.first()
    asa_stats = AsaVpnConnectedUsers.objects.all().order_by('name')
    timecutoff = timezone.now() - timedelta(days=7)
    new_svcacts = SvcActExpiry.objects.filter(created_at__gte=timecutoff)
    new_certalerts = CertExpiry.objects.filter(created_at__gte=timecutoff)
    new_ciscoadvisory = CiscoAdvisory.objects.filter(created_at__gte=timecutoff)
    site_changes = SiteChanges.objects.order_by('-created_at')[:10]
    asastats = []
    for asa in asa_stats:
        detaildict = {
            'name' : asa.name,
            'connected' : asa.connected,
            'load' : asa.load,
            }
        asastats.append(detaildict)
    return render(request, 'network_ops_dashboard/dashboard.html', {'statusmessages': statusmessages, 'asastats': asastats, 'site_settings': site_settings, \
                                                                    'new_svcacts': new_svcacts, 'new_certalerts': new_certalerts, 'new_ciscoadvisory': new_ciscoadvisory, \
                                                                    'site_changes': site_changes })

def public_scripts(request):
    site_settings = SiteSettings.objects.first()
    return render(request, 'network_ops_dashboard/public_scripts.html', {'site_settings': site_settings})

def protected_media(request, path, document_root=None, show_indexes=False):
    if request.user.is_authenticated and request.user.groups.filter(name='net-admin').exists():
        response = HttpResponse(status=200)
        response['Content-Type'] = ''
        response['X-Accel-Redirect'] = '/protected_media/' + quote(path)
        return response
    else:
        return HttpResponse(status=400)