from django import forms
from django.utils.translation import gettext as _
from django.db import models
from network_ops_dashboard.models import *
from network_ops_dashboard.inventory.models import *
from network_ops_dashboard.f5lb.models import *
import json

# Create your forms here.
 
class F5LBMopVipCertRenewForm(forms.ModelForm):
	class Meta:
		model = F5LBMopVipCertRenew
		fields = ('name', 'status', 'device', 'virtual_server', 'ssl_policy', \
            'cert_name', 'cert_key_name', 'cert_key_pass', 'cert_file', 'cert_key_file')
	F5LB_MOP_CHOICES = (
    ("Planned", "Planned"),
    ("Completed", "Completed"),
    ("Cancelled", "Cancelled"),
    ("Running", "Running"),
    ("Closed", "Closed"),
    )
	name = forms.CharField(label="Name:", help_text="CRQ# (If Applicable) + a given name for MOP/VIP/Change. (No Spaces!).", required=True)
	status = forms.ChoiceField(label="Status:", choices=F5LB_MOP_CHOICES, required=True)
	device = forms.ModelChoiceField(label="Device:", queryset=Inventory.objects.filter(device_tag__name__exact='F5LB'), required=True)
	virtual_server = forms.ChoiceField(
		label="Virtual Server Name:",
		choices=[],
		required=True
		)
	ssl_policy = forms.ChoiceField(
		label="SSL Profile Name:",
		choices=[],
		required=True
		)
	cert_name = forms.CharField(label="New Cert Name:", required=True)
	cert_key_name = forms.CharField(label="New Cert Key Name:", required=True)
	cert_key_pass = forms.CharField(label="Cert Key Pass:", required=False, widget=forms.PasswordInput(render_value = True))
	cert_file = forms.FileField(label="Certificate File:", required=True)
	cert_key_file = forms.FileField(label="Certificate Key File:", required=True)
	def __init__(self, *args, **kwargs):
		super(F5LBMopVipCertRenewForm, self).__init__(*args, **kwargs)
		device_id = None
		if 'device' in self.data:
			# Coming from POST User chaning device or submitting form
			try:
				device_id = int(self.data.get('device'))
			except (ValueError, TypeError):
				pass
		elif self.instance and self.instance.device:
			# We are editing the existing record
			device_id = self.instance.device.id
		if device_id:
			config = F5LBConfigOptions.objects.filter(device_id=device_id).first()
			if config:
				try:
					#Load JSON lists
					vs_list = json.loads(config.virtual_servers or '[]')
					ssl_list = json.loads(config.ssl_policies or '[]')
					self.fields['virtual_server'].choices = [(v, v) for v in vs_list]
					self.fields['ssl_policy'].choices = [(p, p) for p in ssl_list]
				except json.JSONDecodeError:
					self.fields['virtual_server'].choices = []
					self.fields['ssl_policy'].choices = []
	def clean_name(self):
		return self.cleaned_data.get('name', '').strip()