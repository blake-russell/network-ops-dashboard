from django import forms
from django.utils.translation import gettext as _
from django.db import models
from network_ops_dashboard.asavpn.models import AsaVpnSettings
from network_ops_dashboard.inventory.models import DeviceTag

# Create your forms here.

class AsaVpnFindAndDiscoForm(forms.Form):
    targetUser = forms.CharField(label="Target User ID:", required=True)
    targetAction = forms.TypedChoiceField(label="Disconnect User?", choices=((False, 'No'), (True, 'Yes')),
                                       coerce=lambda x: x == 'True',
                                       initial='Yes')
    targetDeviceTag = forms.ModelChoiceField(label="DeviceTag:", help_text="Run script with devicetag (N)", queryset=DeviceTag.objects.all(), required=True)
    verifySSL = forms.TypedChoiceField(label="Verify SSL?", choices=((False, 'No'), (True, 'Yes')),
                                       coerce=lambda x: x == 'True',
                                       initial='Yes')
    username1 = forms.CharField(label="Enter your admin username:", help_text="Only required if you want to disconnect target.", required=False)
    password1 = forms.CharField(label="Enter your admin password:", help_text="Only required if you want to disconnect target.", widget=forms.PasswordInput, required=False)
    def clean(self):
        cleaned_data = super().clean()
        target_action = cleaned_data.get("targetAction")
        username1 = cleaned_data.get("username1")
        password1 = cleaned_data.get("username1")

        if target_action == True:
            if not username1:
                self.add_error("username1", "Admin username is required when disconnecting user.")
            if not password1:
                self.add_error("password1", "Admin password is required when disconnecting user.")

class AsaVpnSettingsForm(forms.ModelForm):
    class Meta:
        model = AsaVpnSettings
        fields = ["device_tag", "top_n", "verify_ssl"]
        labels = {
            "device_tag": "Filter by devicetag",
            "top_n": "Show (N) devices",
            "verify_ssl": "Verify SSL",
        }
        widgets = {
            "device_tag": forms.Select(attrs={"class": "form-select"}),
            "top_n": forms.NumberInput(attrs={"class": "form-control", "min": 1, "step": 1}),
            "verify_ssl": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        try:
            self.fields["device_tag"].queryset = DeviceTag.objects.order_by("name")
        except Exception:
            pass