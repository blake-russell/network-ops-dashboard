from __future__ import unicode_literals
from django.contrib.auth.models import User
from django.utils.translation import gettext, gettext_lazy as _
from django_cryptography.fields import encrypt
from django.db import models
from django.conf import settings
from network_ops_dashboard.settings import PROTECTED_MEDIA_ROOT
from network_ops_dashboard.inventory.models import *

# Create your models here.

class OnCallIncident(models.Model):
    STATUS_CHOICES = [('Open', 'Open'), ('Closed', 'Closed')]

    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='Open')
    date_created = models.DateField(auto_now_add=True)
    date_modified = models.DateField(auto_now=True)
    date_closed = models.DateField(null=True, blank=True)
    user_created = models.ForeignKey(User, on_delete=models.SET_NULL, related_name='created_incidents', null=True)
    user_modified = models.ForeignKey(User, on_delete=models.SET_NULL, related_name='modified_incidents', null=True, blank=True)
    headline = models.TextField()
    log = models.TextField()

    def __str__(self):
        return f"{self.headline} - {self.status}"
