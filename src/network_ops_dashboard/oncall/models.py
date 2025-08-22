from __future__ import unicode_literals
from django.contrib.auth.models import User
from django.utils.translation import gettext, gettext_lazy as _
from django_cryptography.fields import encrypt
from django.db import models
from django.conf import settings
from network_ops_dashboard.settings import PROTECTED_MEDIA_ROOT
from network_ops_dashboard.inventory.models import *
from network_ops_dashboard.reports.circuits.models import CircuitTag

# Create your models here.

class OnCallIncident(models.Model):
    STATUS_CHOICES = [('Open', 'Open'), ('Closed', 'Closed'), ('Archived', 'Archived')]

    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='Open')
    date_created = models.DateField(auto_now_add=True)
    date_modified = models.DateField(auto_now=True)
    date_closed = models.DateField(null=True, blank=True)
    date_archived= models.DateField(null=True, blank=True)
    user_created = models.ForeignKey(User, on_delete=models.SET_NULL, related_name='created_incidents', null=True)
    user_modified = models.ForeignKey(User, on_delete=models.SET_NULL, related_name='modified_incidents', null=True, blank=True)
    user_closed = models.ForeignKey(User, on_delete=models.SET_NULL, related_name='closed_incidents', null=True, blank=True)
    headline = models.TextField()
    log = models.TextField()

    def __str__(self):
        return f"{self.headline} - {self.status}"

class OnCallSettings(models.Model):
    circuit_tags = models.ManyToManyField(CircuitTag, blank=True, related_name="oncall_settings")

    show_scheduled_maintenance = models.BooleanField(default=True)
    show_field_advisories = models.BooleanField(default=True)
    show_cert_expiry = models.BooleanField(default=True)
    show_svcacct_expiry = models.BooleanField(default=True)

    show_closed_in_report = models.BooleanField(default=True)
    report_window_days = models.PositiveIntegerField(default=7)

    auto_archive_enabled = models.BooleanField(default=False)
    auto_archive_frequency = models.CharField(
        max_length=10,
        choices=(("daily", "Daily"), ("weekly", "Weekly")),
        default="weekly",
    )
    auto_archive_time = models.CharField(max_length=5, default="08:30")
    auto_archive_weekday = models.PositiveSmallIntegerField(default=0)   # 0=Mon ... 6=Sun

    updated_at = models.DateTimeField(auto_now=True)

    @classmethod
    def load(cls):
        # always load/create the singleton row
        obj, _ = cls.objects.get_or_create(id=1)
        return obj