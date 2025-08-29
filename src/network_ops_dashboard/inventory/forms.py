from django import forms
from django.utils.translation import gettext as _
from network_ops_dashboard.models import *
from network_ops_dashboard.inventory.models import *

# Create your forms here.

class InventoryForm(forms.ModelForm):
    class Meta:
        model = Inventory
        fields = ('name', 'name_lookup', 'site', 'platform', 'serial_number', \
            'ipaddress_mgmt', 'ipaddress_rest', 'ipaddress_gmni', 'port_rest', 'port_netc', \
            'port_gnmi', 'device_tag', 'priority_interfaces', 'creds_ssh', 'creds_rest')
    name = forms.CharField(label="Device Name:", help_text="<br>Enter name that is resolved from mgmt IP excluding<br>the domain/subdomain.", required=True)
    name_lookup = forms.CharField(label="Name Lookup:", help_text="<br>ie: devicename.companyname.com", required=False)
    site = forms.ModelChoiceField(label="Site:", queryset=Site.objects.all(), required=False)
    platform = forms.ModelChoiceField(label="Platform:", queryset=Platform.objects.all(), required=False)
    serial_number = forms.CharField(label="Serial Number:", required=False)
    ipaddress_mgmt = forms.GenericIPAddressField(label="IP Address (MGMT):", initial='0.0.0.0')
    ipaddress_rest = forms.GenericIPAddressField(label="IP Address (REST):", initial='0.0.0.0')
    ipaddress_gmni = forms.GenericIPAddressField(label="IP Address (gNMI):", initial='0.0.0.0')
    port_rest = forms.CharField(label="Port (REST):", initial='0')
    port_netc = forms.CharField(label="Port (NETCONF):", initial='0')
    port_gnmi = forms.CharField(label="Port (gNMI):", initial='0')
    device_tag = forms.ModelMultipleChoiceField(label="Device Tags:", queryset=DeviceTag.objects.all(), widget=forms.SelectMultiple(attrs={'class': 'form-select'}), required=False)
    priority_interfaces = forms.CharField(label="Priority Interfaces:", help_text="<br>ie: GigabitEthernet2/1/1, TenGigabitEthernet1/1/1, etc", required=False)
    creds_ssh = forms.ModelChoiceField(label="SSH Credential:", queryset=NetworkCredential.objects.all(), required=False)
    creds_rest = forms.ModelChoiceField(label="REST Credential:", queryset=NetworkCredential.objects.all(), required=False)

class PlatformForm(forms.ModelForm):
    class Meta:
        model = Platform
        fields = ('manufacturer', 'name', 'PID', 'ansible_namespace', 'netmiko_namespace')
    manufacturer = forms.CharField(label="Manufacturer:", required=True)
    name = forms.CharField(label="Platform Name:", help_text="ie: Nexus C9508", required=True)
    PID = forms.CharField(label="PID:", help_text="ie: N9K-C9508", required=True)
    ansible_namespace = forms.CharField(label="Ansible Namespace:", required=False)
    netmiko_namespace = forms.CharField(label="Netmiko Namespace:", required=False)

class SiteForm(forms.ModelForm):
    class Meta:
        model = Site
        fields = ('name', 'address', 'city', 'zip', 'state', 'poc_name', 'poc_number')
    name = forms.CharField(label="Site Name:", help_text="ie: Dallas DC", required=True)
    address = forms.CharField(label="Steet Address:", required=False)
    city = forms.CharField(label="City:", required=False)
    state = forms.CharField(label="State:", required=False)
    zip = forms.CharField(label="Zipcode:", required=False, initial="0")
    poc_name = forms.CharField(label="POC Name:", required=False)
    poc_number = forms.CharField(label="POC Number:", required=False)

class DeviceTagForm(forms.ModelForm):
    class Meta:
        model = DeviceTag
        fields = ('name',)
    name = forms.CharField(label="Device Tag:", required=True)

class NetworkCredentialForm(forms.ModelForm):
    class Meta:
        model = NetworkCredential
        fields = ('username_search_field', 'username', 'password', 'api_key')

    username_search_field = forms.CharField(label="Credential Name:", max_length=100, required=True)
    username = forms.CharField(label="Username:", max_length=100, required=False)
    password = forms.CharField(label="Password:", max_length=100,widget=forms.PasswordInput(render_value=True),required=False)
    api_key = forms.CharField(label="API Key:", help_text="Enter API Key or User/Pass Combo.", max_length=300, widget=forms.PasswordInput(render_value=True), required=False)

    def clean(self):
        cleaned_data = super().clean()
        username = cleaned_data.get("username")
        password = cleaned_data.get("password")
        api_key = cleaned_data.get("api_key")

        if not api_key:
            # API key not provided → require username & password
            if not username:
                self.add_error("username", "Username is required if no API key is provided.")
            if not password:
                self.add_error("password", "Password is required if no API key is provided.")

        return cleaned_data