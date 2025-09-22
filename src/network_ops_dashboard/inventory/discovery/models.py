import uuid
from django.contrib.auth import get_user_model
from django.db import models
from django.utils import timezone
from django.conf import settings

# Create your models here.

User = get_user_model()

class DiscoveryJob(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending"
        RUNNING = "running"
        DONE    = "done"
        ERROR   = "error"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    params = models.JSONField(default=dict)
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.PENDING)
    started_at = models.DateTimeField(null=True, blank=True)
    finished_at = models.DateTimeField(null=True, blank=True)
    result_summary = models.TextField(blank=True, default="")
    result_count = models.PositiveIntegerField(default=0)
    log = models.TextField(blank=True, default="")
    processed_count = models.PositiveIntegerField(default=0)
    ignored_count = models.PositiveIntegerField(default=0)
    completed = models.BooleanField(default=False)

    def mark_running(self):
        self.status = self.Status.RUNNING
        self.started_at = timezone.now()
        self.save(update_fields=["status", "started_at"])

    def mark_done(self, count:int, summary:str=""):
        self.status = self.Status.DONE
        self.finished_at = timezone.now()
        self.result_count = count
        self.result_summary = summary
        self.save(update_fields=["status","finished_at","result_count","result_summary"])

    def mark_error(self, msg:str):
        self.status = self.Status.ERROR
        self.finished_at = timezone.now()
        self.log = (self.log + "\n" + msg).strip()
        self.save(update_fields=["status","finished_at","log"])

class DiscoveredDevice(models.Model):
    # tied to a job so results live in DB
    job = models.ForeignKey(DiscoveryJob, on_delete=models.CASCADE, related_name="devices")
    ip = models.GenericIPAddressField()
    hostname = models.CharField(max_length=200, blank=True, default="")
    platform_guess = models.CharField(max_length=200, blank=True, default="")
    discovered_via = models.CharField(max_length=50, blank=True, default="ping")  # ping / snmp / ssh
    last_seen = models.DateTimeField(default=timezone.now)
    raw = models.JSONField(default=dict)   # store full payload returned by discovery
    added_to_inventory = models.BooleanField(default=False)
    ignored = models.BooleanField(default=False)
    
    def __str__(self):
        return f"{self.ip} ({self.hostname})"