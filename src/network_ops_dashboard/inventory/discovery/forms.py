from django import forms
from network_ops_dashboard.models import NetworkCredential

class DiscoveryForm(forms.Form):
    targets = forms.CharField(
        label="Targets (CIDR, IPs, ranges, hostnames)",
        widget=forms.Textarea(attrs={
            "rows":3,
            "placeholder":"10.0.0.0/24\nhost1.example.com\n10.0.0.5-10.0.0.25"
        })
    )
    scan_kind = forms.ChoiceField(
        choices=[("snmp","SNMP"),("ssh","SSH")],
        initial="snmp",
        label="Discovery Method"
    )
    snmp_community = forms.CharField(
        label="SNMP Community",
        required=False
    )
    credential = forms.ModelChoiceField(
        label="SSH Credential",
        queryset=NetworkCredential.objects.all(),
        required=False
    )
    timeout = forms.IntegerField(label="Timeout (s)", min_value=1, initial=5)
    verify_ssl = forms.BooleanField(label="Verify SSL (if HTTPS used)", required=False)

    def clean(self):
        cleaned = super().clean()
        kind = cleaned.get("scan_kind")

        if kind == "snmp" and not cleaned.get("snmp_community"):
            raise forms.ValidationError("SNMP discovery requires a community string.")
        if kind == "ssh" and not cleaned.get("credential"):
            raise forms.ValidationError("SSH discovery requires a credential.")

        return cleaned