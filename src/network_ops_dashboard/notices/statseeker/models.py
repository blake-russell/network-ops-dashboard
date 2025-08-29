from django.db import models
from django.utils import timezone
from network_ops_dashboard.inventory.models import Inventory
from network_ops_dashboard.models import NetworkCredential

# Create your models here.

class StatseekerSettings(models.Model):
    enabled               = models.BooleanField(default=False)
    credential            = models.ForeignKey(
        NetworkCredential, null=True, blank=True,
        on_delete=models.SET_NULL, related_name="statseeker_api_cred"
    )
    base_url = models.TextField(help_text="https://statseeker.example.com", blank=True, null=True, default="")
    verify_ssl = models.BooleanField(default=False)
    tracked_devices = models.ManyToManyField(Inventory, blank=True, related_name="statseeker_tracked")
    top_n = models.PositiveIntegerField(default=10)
    min_interval_minutes = models.PositiveIntegerField(default=5)
    error_pct_threshold = models.DecimalField(max_digits=5, decimal_places=2, default=1.00, help_text="% errors over last window")
    include_device_down = models.BooleanField(default=True)
    include_if_down = models.BooleanField(default=True)
    include_if_errors = models.BooleanField(default=True)
    updated_at = models.DateTimeField(auto_now=True)

    @classmethod
    def load(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj


class StatseekerAlert(models.Model):
    TYPE_CHOICES = [
        ("DEVICE_DOWN", "Device Down"),
        ("IF_DOWN", "Interface Down"),
        ("IF_ERRORS", "Interface Errors"),
    ]
    device = models.ForeignKey(Inventory, null=True, on_delete=models.SET_NULL)
    alert_type = models.CharField(max_length=16, choices=TYPE_CHOICES)
    interface_name = models.CharField(max_length=128, blank=True, default="")
    severity = models.CharField(max_length=16, blank=True, default="")  # optional
    metric_value = models.DecimalField(max_digits=12, decimal_places=3, null=True, blank=True)
    started_at = models.DateTimeField(default=timezone.now)
    last_seen_at = models.DateTimeField(default=timezone.now)
    active = models.BooleanField(default=True, db_index=True)
    note = models.TextField(blank=True, default="")

    class Meta:
        indexes = [
            models.Index(fields=["active", "alert_type"]),
            models.Index(fields=["device"]),
        ]

    def __str__(self):
        base = f"{self.device or '(unknown)'} {self.alert_type}"
        return f"{base} {self.interface_name}".strip()