from django import forms
from .models import StatseekerSettings
from network_ops_dashboard.inventory.models import Inventory
from network_ops_dashboard.models import NetworkCredential


class StatseekerSettingsForm(forms.ModelForm):
    class Meta:
        model = StatseekerSettings
        fields = [
            "enabled", "credential", "base_url", "verify_ssl",
            "tracked_devices", "top_n", "min_interval_minutes",
            "error_pct_threshold", "include_device_down", "include_if_down", "include_if_errors",
        ]
        labels = {
            "enabled": "Enable Statseeker Alerts",
            "credential": "API Token (NetworkCredential)",
            "base_url": "Statseeker URL",
            "verify_ssl": "Verify SSL",
            "tracked_devices": "Monitored Devices",
            "top_n": "Show up to N alerts",
            "min_interval_minutes": "Collector min interval (minutes)",
            "error_pct_threshold": "Error % threshold",
            "include_device_down": "Include device down",
            "include_if_down": "Include interface down",
            "include_if_errors": "Include high error rate",
        }
        widgets = {
            "enabled": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "credential": forms.Select(attrs={"class": "form-select"}),
            "base_url": forms.TextInput(attrs={"class": "form-control", "placeholder": "https://..."}),
            "verify_ssl": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "tracked_devices": forms.SelectMultiple(attrs={"class": "form-select", "size": 8}),
            "top_n": forms.NumberInput(attrs={"class": "form-control", "min": 1}),
            "min_interval_minutes": forms.NumberInput(attrs={"class": "form-control", "min": 1}),
            "error_pct_threshold": forms.NumberInput(attrs={"class": "form-control", "min": 0, "step": "0.1"}),
            "include_device_down": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "include_if_down": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "include_if_errors": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        try:
            self.fields["credential"].queryset = NetworkCredential.objects.order_by("name")
        except Exception:
            pass
        # If you’d like to pre-filter available devices, do it here:
        self.fields["tracked_devices"].queryset = Inventory.objects.all().order_by("name")
        self.fields["tracked_devices"].help_text = "Choose devices to watch. Their priority_interfaces field determines which interfaces to evaluate for IF_DOWN/IF_ERRORS."

