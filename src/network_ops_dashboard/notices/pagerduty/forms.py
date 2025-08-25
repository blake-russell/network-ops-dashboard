from django import forms
from .models import PagerDutySettings
from network_ops_dashboard.inventory.models import NetworkCredential

class PagerDutySettingsForm(forms.ModelForm):
    class Meta:
        model = PagerDutySettings
        fields = ["enabled", "credential", "service_ids_csv", "urgency_filter",
                  "top_n", "min_interval_minutes", "verify_ssl"]
        labels = {
            "enabled": "Enable PagerDuty Incidents",
            "credential": "API Token (NetworkCredential)",
            "service_ids_csv": "Filter by Service IDs (comma separated)",
            "urgency_filter": "Urgency (high/low)",
            "top_n": "Show up to (N) incidents",
            "min_interval_minutes": "Interval (min)",
            "verify_ssl": "Verify SSL",
        }
        widgets = {
            "enabled": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "credential": forms.Select(attrs={"class": "form-select"}),
            "service_ids_csv": forms.TextInput(attrs={"class": "form-control", "placeholder": "PXXXX1,PXXXX2"}),
            "urgency_filter": forms.TextInput(attrs={"class": "form-control", "placeholder": "high or low"}),
            "top_n": forms.NumberInput(attrs={"class": "form-control", "min": 1}),
            "min_interval_minutes": forms.NumberInput(attrs={"class": "form-control", "min": 1}),
            "verify_ssl": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        try:
            self.fields["credential"].queryset = NetworkCredential.objects.order_by("name")
        except Exception:
            pass
