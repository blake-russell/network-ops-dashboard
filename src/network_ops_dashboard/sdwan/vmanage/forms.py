from django import forms
from django.core.exceptions import ValidationError

from network_ops_dashboard.sdwan.vmanage.models import SdwanSettings
from network_ops_dashboard.inventory.models import Inventory


class SDWANSettingsForm(forms.ModelForm):
    class Meta:
        model = SdwanSettings
        fields = [
            "card_enabled",
            "host",
            "purge_path_stats",
            "top_n",
            "last_n",
            "verify_ssl",
        ]
        labels = {
            "host": "vManage Host (Inventory)",
            "purge_path_stats": "Purge older than (N) Hours",
            "top_n": "Show (N) Sites",
            "last_n": "Show Last (N) Minutes",
            "verify_ssl": "Verify SSL",
        }
        widgets = {
            "card_enabled": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "host": forms.Select(attrs={"class": "form-select"}),      
            "purge_path_stats": forms.NumberInput(attrs={"class": "form-control", "min": 1}),
            "top_n": forms.NumberInput(attrs={"class": "form-control", "min": 1, "step": 1}),
            "last_n": forms.NumberInput(attrs={"class": "form-control", "min": 1, "step": 1}),
            "verify_ssl": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        try:
            self.fields["host"].queryset = Inventory.objects.all().order_by("name")
        except Exception:
            pass

        # Sensible defaults if instance is new
        if not self.instance.pk:
            self.initial.setdefault("card_enabled", False)
            self.initial.setdefault("purge_path_stats", 4)
            self.initial.setdefault("top_n", 10)
            self.initial.setdefault("last_n", 30)
            self.initial.setdefault("verify_ssl", False)