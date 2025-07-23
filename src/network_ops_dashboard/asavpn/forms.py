from django import forms
from django.utils.translation import gettext as _
from django.db import models
from network_ops_dashboard.asavpn.models import *

# Create your forms here.

class AsaVpnFindAndDiscoForm(forms.Form):
	TARGET_ACTION_CHOICES = ((False, 'No'), (True, 'Yes'))
	targetUser = forms.CharField(label="Target User LANID:", required=True)
	targetAction = forms.ChoiceField(label="Disconnect User?", choices=TARGET_ACTION_CHOICES)
	username1 = forms.CharField(label="Enter your admin username:", help_text="Only required if you want to disconnect target.", required=False)
	password1 = forms.CharField(label="Enter your admin password:", help_text="Only required if you want to disconnect target.", widget=forms.PasswordInput,  required=False)
	def clean(self):
		cleaned_data = super().clean()
		target_action = cleaned_data.get("targetAction")
		username1 = cleaned_data.get("username1")
		password1 = cleaned_data.get("username1")

		if target_action == 'True':
			if not username1:
				self.add_error("username1", "Admin username is required when disconnecting user.")
			if not password1:
				self.add_error("password1", "Admin password is required when disconnecting user.")