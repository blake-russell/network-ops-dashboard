from __future__ import unicode_literals
from django.contrib.auth.models import User
from django.utils.translation import gettext, gettext_lazy as _
from django_cryptography.fields import encrypt
from django.db import models
from django.conf import settings
from network_ops_dashboard.models import NetworkCredential

# Create your models here.

class Site(models.Model):
    class Meta:
        ordering = ['name']
    name = models.CharField(max_length=100)
    address = models.CharField(max_length=100)
    city = models.CharField(max_length=100)
    zip = models.IntegerField()
    state = models.CharField(max_length=100)
    poc_name = models.CharField(max_length=100)
    poc_number = models.CharField(max_length=100)
    def __str__(self):
        return str(self.name)
    
class Platform(models.Model):
    class Meta:
        ordering = ['manufacturer']
    manufacturer = models.CharField(max_length=100)
    name = models.CharField(max_length=100)
    PID = models.CharField(max_length=100)
    ansible_namespace = models.CharField(max_length=100, blank=True)
    netmiko_namespace = models.CharField(max_length=100, blank=True)
    def __str__(self):
        return str(self.manufacturer + ' ' + self.name)
    
class DeviceTag(models.Model):
    class Meta:
        ordering = ['name']
    name = models.CharField(max_length=100)
    def __str__(self):
        return str(self.name)
    
class Inventory(models.Model):
    class Meta:
        ordering = ['name']
    name = models.CharField(max_length=100)
    name_lookup = models.CharField(max_length=200, blank=True, default="")
    site = models.ForeignKey(Site, null=True, on_delete=models.SET_NULL, blank=True)
    platform = models.ForeignKey(Platform, null=True, on_delete=models.SET_NULL, blank=True)
    serial_number = models.CharField(max_length=50)
    ipaddress_mgmt = models.GenericIPAddressField(protocol='IPv4', null=True, blank=True)
    ipaddress_rest = models.GenericIPAddressField(protocol='IPv4', null=True, blank=True)
    ipaddress_gnmi = models.GenericIPAddressField(protocol='IPv4', null=True, blank=True)
    port_rest = models.IntegerField(default=0)
    port_netc = models.IntegerField(default=0)
    port_gnmi = models.IntegerField(default=0)
    device_tag = models.ManyToManyField(DeviceTag)
    priority_interfaces = models.CharField(max_length=750, blank=True)
    creds_ssh = models.ForeignKey(NetworkCredential, null=True, on_delete=models.SET_NULL, blank=True, related_name="inventory_creds_ssh")
    creds_rest = models.ForeignKey(NetworkCredential, null=True, on_delete=models.SET_NULL, blank=True, related_name="inventory_creds_rest")
    def get_priority_interfaces(self):
        return [k.strip() for k in self.priority_interfaces.split(',') if k.strip()]
    def set_priority_interfaces(self, priority_interfaces_list):
        self.get_priority_interfaces = ','.join(priority_interfaces_list)
    def __str__(self):
        return str(self.name)