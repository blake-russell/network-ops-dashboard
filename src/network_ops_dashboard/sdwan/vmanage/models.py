from django.db import models
from django.utils import timezone
from django.conf import settings
from network_ops_dashboard.inventory.models import Inventory

# Create your models here.

class SdwanSettings(models.Model):
    card_enabled = models.BooleanField(default=False)
    host = models.ForeignKey(Inventory, null=True, on_delete=models.SET_NULL, related_name="sdwan_vmanage_host")
    verify_ssl = models.BooleanField(default=False)
    top_n = models.PositiveIntegerField(default=10, help_text="Show top N sites.")
    last_n = models.PositiveIntegerField(default=15, help_text="Show last N minutes.") # minutes
    enable_latency_jitter = models.BooleanField(default=True) # (not currently in use)
    latency_threshold = models.IntegerField(default=120) # ms (not currently in use)
    loss_threshold = models.DecimalField(max_digits=5, decimal_places=2, default=1.00) # % (not currently in use)
    purge_path_stats = models.PositiveIntegerField(default=6, help_text="Purge SdwanPathStat entries older than x hours.")
    updated_at = models.DateTimeField(auto_now=True)

    @classmethod
    def load(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj

class SdwanPathStat(models.Model):
    # identity
    tunnel_id = models.CharField(max_length=200, db_index=True)
    local_system_ip = models.GenericIPAddressField(null=True)
    remote_system_ip = models.GenericIPAddressField(null=True)
    local_color = models.CharField(max_length=32, default="")
    remote_color = models.CharField(max_length=32, default="")
    # optional
    device_model = models.CharField(max_length=64, blank=True, default="")
    host_name = models.CharField(max_length=128, blank=True, default="")
    proto = models.CharField(max_length=16, blank=True, default="")
    # metrics
    latency_ms = models.FloatField(null=True)
    jitter_ms  = models.FloatField(null=True)
    loss_pct   = models.FloatField(null=True)
    vqoe_score = models.FloatField(null=True)
    # counters
    tx_pkts = models.BigIntegerField(null=True)
    rx_pkts = models.BigIntegerField(null=True)
    tx_octets = models.BigIntegerField(null=True)
    rx_octets = models.BigIntegerField(null=True)
    # state & time
    state = models.CharField(max_length=16, blank=True, default="")
    entry_time = models.DateTimeField(null=True)
    collected_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["tunnel_id", "entry_time"]),
            models.Index(fields=["local_system_ip", "remote_system_ip"]),
        ]

    def __str__(self):
        return str(f"{self.collected_at} - {self.tunnel_id}")