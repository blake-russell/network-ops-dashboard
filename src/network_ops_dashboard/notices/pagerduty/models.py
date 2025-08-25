from django.db import models
from django.utils import timezone
from network_ops_dashboard.models import NetworkCredential

# Create your models here.

class PagerDutySettings(models.Model):
    enabled = models.BooleanField(default=False)
    credential = models.ForeignKey(NetworkCredential,
        null=True, blank=True, on_delete=models.SET_NULL,
        related_name="pagerduty_api_cred",
    )
    service_ids_csv = models.TextField(blank=True, default="")   # comma-separated PD service IDs
    urgency_filter = models.CharField(max_length=16, blank=True, default="")  # "", "high", "low"
    top_n = models.PositiveIntegerField(default=10)
    verify_ssl = models.BooleanField(default=False)

    # collection throttle
    min_interval_minutes = models.PositiveIntegerField(default=5)
    updated_at = models.DateTimeField(auto_now=True)

    @classmethod
    def load(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj


class PagerDutyIncident(models.Model):
    incident_id = models.CharField(max_length=64, unique=True, db_index=True)
    title = models.CharField(max_length=255)
    status = models.CharField(max_length=32, db_index=True)  # triggered | acknowledged | resolved
    urgency = models.CharField(max_length=16, blank=True, default="")
    service_name = models.CharField(max_length=128, blank=True, default="")
    service_id = models.CharField(max_length=64, blank=True, default="")
    html_url = models.URLField(blank=True, default="")
    created_at = models.DateTimeField()
    last_status_at = models.DateTimeField()
    active = models.BooleanField(default=True, db_index=True)  # False when PD says resolved

    # convenience
    summary = models.TextField(blank=True, default="")
    assignments = models.TextField(blank=True, default="")

    synced_at = models.DateTimeField(default=timezone.now)

    class Meta:
        indexes = [
            models.Index(fields=["active", "status"]),
            models.Index(fields=["service_name"]),
        ]

    def __str__(self):
        return f"{self.incident_id} {self.status} {self.title[:40]}"
