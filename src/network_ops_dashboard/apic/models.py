from __future__ import unicode_literals
from django.utils.translation import gettext, gettext_lazy as _
from django.db import models
from django.conf import settings
from network_ops_dashboard.inventory.models import *

# Create your models here.

class APICMopInterface(models.Model):
    class Meta:
        ordering = ['intfdesc']
    user = models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.CASCADE)
    intfprofile = models.CharField(max_length=100, unique=False, blank=True)
    intfselector = models.CharField(max_length=100, unique=False, blank=True)
    intfipg = models.CharField(max_length=100, unique=False, blank=True)
    intffromport = models.CharField(max_length=100, unique=False, blank=True)
    intftoport = models.CharField(max_length=100, unique=False, blank=True)
    intfdesc = models.CharField(max_length=100, unique=False, blank=True)
    device = models.ForeignKey(Inventory, null=True, on_delete=models.SET_NULL, blank=True)
    def __str__(self):
        return str(self.intfdesc)
    
class APICMopCreateInterface(models.Model):
    class Meta:
        ordering = ['name']
    APIC_PLAYBOOK_CHOICES = (
    ("Planned", "Planned"),
    ("Completed", "Completed"),
    ("Cancelled", "Cancelled"),
    ("Running", "Running"),
    ("Closed", "Closed"),
    )
    name = models.CharField(max_length=100, unique=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.CASCADE)
    status = models.CharField(choices=APIC_PLAYBOOK_CHOICES, default="Planned", max_length=100)
    device = models.ForeignKey(Inventory, null=True, on_delete=models.SET_NULL, blank=True)
    interfaces = models.ManyToManyField(APICMopInterface)
    def __str__(self):
        return str(self.name)
    
class APICConfigOptions(models.Model):
    class Meta:
        ordering = ['device']
    device = models.ForeignKey(Inventory, null=True, on_delete=models.SET_NULL)
    interface_profiles = models.TextField(null=True, blank=True)
    interface_policy_groups = models.TextField(null=True, blank=True)
    def __str__(self):
        return str(self.device)