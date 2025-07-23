from django import forms
from django.utils.translation import gettext as _
from network_ops_dashboard.models import *
from network_ops_dashboard.inventory.models import *
from network_ops_dashboard.apic.models import *
import json

# Create your forms here.
class APICMopCreateInterfaceAddForm(forms.ModelForm):
	class Meta:
		model = APICMopCreateInterface
		fields = ('name', 'status', 'device')
	name = forms.CharField(label="Name:", help_text="CRQ# (If Applicable) + a given name for MOP/VIP/Change. (No Spaces!).", required=True)
	status = forms.ChoiceField(label="Status:", choices=APIC_MOP_CHOICES, required=True)
	device = forms.ModelChoiceField(label="Device:", queryset=Inventory.objects.filter(device_tag__name__exact='APIC'), required=True)
	def clean_name(self):
		return self.cleaned_data.get('name', '').strip()
	
class APICMopCreateInterfaceEditForm(forms.ModelForm):
	class Meta:
		model = APICMopCreateInterface
		fields = ('name', 'status', 'device', 'interfaces')
	name = forms.CharField(label="Name:", help_text="CRQ# (If Applicable) + a given name for MOP/VIP/Change. (No Spaces!).", required=True)
	status = forms.ChoiceField(label="Status:", choices=APIC_MOP_CHOICES, required=True)
	device = forms.ModelChoiceField(label="Device:", queryset=Inventory.objects.filter(device_tag__name__exact='APIC'), required=True)
	interfaces = forms.ModelMultipleChoiceField(label="Interfaces:", queryset=APICMopInterface.objects.none(), widget=forms.SelectMultiple(attrs={'class': 'form-select', 'size': '10'}), required=False)
	def __init__(self, *args, **kwargs):
		user = kwargs.pop('user', None)
		super().__init__(*args, **kwargs)
		if user:
			self.fields['interfaces'].queryset = APICMopInterface.objects.filter(user=user)
			'''
			if user.groups.filter(name='site-admin').exists():
				self.fields['interfaces'].queryset = APICMopInterface.objects.all()
			else:
				self.fields['interfaces'].queryset = APICMopInterface.objects.filter(user=user)
			'''
		if self.instance and self.instance.pk and self.instance.interfaces.exists():
			self.fields['device'].disabled = True # Disable device field if interfaces exist
	def clean_device(self):
		if self.instance and self.instance.pk and self.instance.interfaces.exists():
			# Return the existing device value to block changes in POST
			return self.instance.device
		return self.cleaned_data['device']
	def clean_name(self):
		return self.cleaned_data.get('name', '').strip()

class APICMopInterfaceForm(forms.ModelForm):
	class Meta:
		model = APICMopInterface
		fields = ('device', 'intfdesc', 'intfprofile', 'intfselector', 'intfipg', \
            'intffromport', 'intftoport')
	device = forms.ModelChoiceField(label="Device:", queryset=Inventory.objects.filter(device_tag__name__exact='APIC'), required=True)
	intfdesc = forms.CharField(label="Interface Description:", required=True)
	intfprofile = forms.ChoiceField(
		label="Interface Profile:",
		choices=[],
		required=True
		)
	intfselector = forms.CharField(label="Interface Selector:", required=True)
	intfipg = forms.ChoiceField(
		label="Interface Profile Group:",
		choices=[],
		required=True
		)
	intffromport = forms.CharField(label="From Port:", required=True)
	intftoport = forms.CharField(label="To Port:", required=True)
	
	def __init__(self, *args, **kwargs):
		readonly_device = kwargs.pop('readonly_device', False)
		super().__init__(*args, **kwargs)
		device_id = None
		# Check POST data
		if 'device' in self.data:
			try:
				device_id = int(self.data.get('device'))
			except (ValueError, TypeError):
				pass
		# Check instance from ModelForm
		elif self.instance and self.instance.device:
			device_id = self.instance.device.id
		# Check initial data
		elif 'initial' in kwargs and 'device' in kwargs['initial']:
			device = kwargs['initial']['device']
			if hasattr(device, 'id'):
				device_id = device.id
			else:
				try:
					device_id = int(device)
				except (ValueError, TypeError):
					pass
		if device_id:
			config = APICConfigOptions.objects.filter(device_id=device_id).first()
			if config:
				try:
					#Load JSON lists
					ipf_list = json.loads(config.interface_profiles or '[]')
					ipg_list = json.loads(config.interface_policy_groups or '[]')
					self.fields['intfprofile'].choices = [(ipf, ipf) for ipf in ipf_list]
					self.fields['intfipg'].choices = [(ipg, ipg) for ipg in ipg_list]
				except json.JSONDecodeError:
					self.fields['intfprofile'].choices = []
					self.fields['intfipg'].choices = []
		# Hide Device as we don't want users to change this field.
		if readonly_device:
			self.fields['device'].widget.attrs.update({
				'readonly': True,
				'class': 'readonly-device',
				'style': 'pointer-events: none; background-color: #e9ecef;'
			})
	def clean_name(self):
		return self.cleaned_data.get('intfdesc', '').strip()