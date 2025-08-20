from django import forms
from django.core.exceptions import ValidationError

from network_ops_dashboard.sdwan.vmanage.models import SdwanSettings
from network_ops_dashboard.inventory.models import Inventory


class SDWANSettingsForm(forms.ModelForm):
    class Meta:
        model = SdwanSettings
        fields = [
            "host",
            "card_enabled",
            "top_n",
            "latency_threshold",
            "loss_threshold",
        ]
        labels = {
            "host": "vManage Host (Inventory)",
            "top_n": "Show (N) Sites",
            "latency_threshold": "Latency threshold (ms)",
            "loss_threshold": "Loss threshold (%)",
        }
        widgets = {
            "host": forms.Select(attrs={"class": "form-select"}),
            "card_enabled": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "top_n": forms.NumberInput(attrs={"class": "form-control", "min": 1, "step": 1}),
            "latency_threshold": forms.NumberInput(attrs={"class": "form-control", "min": 0}),
            "loss_threshold": forms.NumberInput(attrs={"class": "form-control", "min": 0, "step": "0.1"}),
        }


    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        try:
            self.fields["host"].queryset = Inventory.objects.all().order_by("name")
        except Exception:
            pass

        # Sensible defaults if instance is new
        if not self.instance.pk:
            self.initial.setdefault("card_enabled", True)
            self.initial.setdefault("latency_threshold", 120)
            self.initial.setdefault("loss_threshold", 1.0)

    def clean_latency_threshold(self):
        v = self.cleaned_data["latency_threshold"]
        if v is None or v < 0:
            raise ValidationError("Latency threshold must be ≥ 0.")
        return v

    def clean_loss_threshold(self):
        v = self.cleaned_data["loss_threshold"]
        if v is None or v < 0:
            raise ValidationError("Loss threshold must be ≥ 0.")
        return v