from __future__ import unicode_literals
from django.utils.translation import gettext, gettext_lazy as _
from django_cryptography.fields import encrypt
from django.db import models
from django.conf import settings
from django.utils import timezone

# Create your models here.
 
class CompanyChanges(models.Model):
    team_name = models.CharField(max_length=100)
    change_id = models.CharField(max_length=100, unique=True)
    scheduled_start = models.DateTimeField()
    scheduled_end = models.DateTimeField()
    location = models.CharField(max_length=100)
    summary = models.TextField()

    # Optional fields
    class_type = models.CharField(max_length=100, blank=True, null=True) 
    risk = models.CharField(max_length=100, blank=True, null=True)
    group = models.CharField(max_length=100, blank=True, null=True)
    manager = models.CharField(max_length=100, blank=True, null=True)

    # Catch-all for anything else
    metadata = models.JSONField(blank=True, null=True)

    imported_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.change_id}_({self.team_name})"