from __future__ import unicode_literals
from django.contrib.auth.models import User
from django.utils.translation import gettext, gettext_lazy as _
from django.core.files.storage import FileSystemStorage
from django_cryptography.fields import encrypt
from django.db import models
from django.conf import settings
from network_ops_dashboard.settings import PROTECTED_MEDIA_ROOT
from network_ops_dashboard.inventory.models import *

# Create your models here.

class F5LBMopVipCertRenew(models.Model):
    class Meta:
        ordering = ['name']
    def cert_file_path(instance, filename):
        # file will be uploaded to MEDIA_ROOT/f5lb/f5lb_mop_vipcertrenew/<name>/<filename>
        return f'f5lb/mop_vipcertrenew/{instance.name}/{filename}'
    def cert_key_file_path(instance, filename):
        # file will be uploaded to PROTECTED_MEDIA_ROOT/f5lb/f5lb_mop_vipcertrenew/<name>/<filename>
        return f'f5lb/mop_vipcertrenew/{instance.name}/{filename}'
    F5LB_MOP_CHOICES = (
    ("Planned", "Planned"),
    ("Completed", "Completed"),
    ("Cancelled", "Cancelled"),
    ("Running", "Running"),
    ("Closed", "Closed"),
    )
    name = models.CharField(max_length=100, unique=True)
    status = models.CharField(choices=F5LB_MOP_CHOICES, default="Planned", max_length=100)
    device = models.ForeignKey(Inventory, null=True, on_delete=models.SET_NULL, blank=True)
    virtual_server = models.CharField(max_length=100, blank=True)
    ssl_policy = models.CharField(max_length=100, blank=True)
    cert_name = models.CharField(max_length=100, blank=True)
    cert_key_name = models.CharField(max_length=100, blank=True)
    cert_key_pass = encrypt(models.CharField(max_length=100, blank=True))
    cert_file = models.FileField(upload_to=cert_file_path)
    cert_key_file = models.FileField(upload_to=cert_key_file_path, storage=FileSystemStorage(location=PROTECTED_MEDIA_ROOT, base_url='/uploads'), blank=True, null=True)
    def save(self, *args, **kwargs):
        self.full_clean() # performs regular validation then clean()
        super(F5LBMopVipCertRenew, self).save(*args, **kwargs)
    def clean(self):
        if self.name: 
            self.name = self.name.strip()
    def __str__(self):
        return str(self.name)
    
class F5LBConfigOptions(models.Model):
    class Meta:
        ordering = ['device']
    device = models.ForeignKey(Inventory, null=True, on_delete=models.SET_NULL)
    virtual_servers = models.TextField(null=True, blank=True)
    ssl_policies = models.TextField(null=True, blank=True)
    def __str__(self):
        return str(self.device)