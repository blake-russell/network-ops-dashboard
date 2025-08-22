from __future__ import unicode_literals
from django.utils.translation import gettext, gettext_lazy as _
from django_cryptography.fields import encrypt
from django.db import models
from django.conf import settings
from network_ops_dashboard.inventory.models import DeviceTag

# Create your models here.

class AsaVpnDiscoLog(models.Model):
    class Meta:
        ordering = ['logoutput']
    username = models.CharField(max_length=50)
    logoutput = models.CharField(max_length=200)
    def __str__(self):
        return str(self.username + ' - ' + self.logoutput)
    
class AsaVpnConnectedUsers(models.Model):
    class Meta:
        ordering = ['name']
    name = models.CharField(max_length=50)
    connected = models.CharField(max_length=50)
    load = models.CharField(max_length=50)
    def __str__(self):
        return str(self.name)
    
class AsaVpnSettings(models.Model):
    device_tag = models.ForeignKey(
        DeviceTag,
        null=True, blank=True,
        on_delete=models.SET_NULL,
        help_text=""
    )
    top_n = models.PositiveIntegerField(default=10, help_text="Show (N) devices.")
    verify_ssl = models.BooleanField(default=False)
    updated_at = models.DateTimeField(auto_now=True)

    @classmethod
    def load(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj

    def __str__(self):
        return f"ASA VPN Settings (tag={self.device_tag or 'ALL'}, top_n={self.top_n})"