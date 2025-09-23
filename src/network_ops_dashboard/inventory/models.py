from __future__ import unicode_literals
from django.utils.translation import gettext, gettext_lazy as _
from django_cryptography.fields import encrypt
from django.db import models
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
from django.conf import settings
from network_ops_dashboard.models import NetworkCredential

# Create your models here.

class Site(models.Model):
    class Meta:
        ordering = ['name']
    TIMEZONE_CHOICES = (
    ("PST", "PST"),
    ("MST", "MST"),
    ("CST", "CST"),
    ("EST", "EST"),
    )
    SITE_TYPE_CHOICES = (
    ("Business Office", "Business Office"),
    ("Customer Care Center", "Customer Care Center"),
    ("Datacenter", "Datacenter"),
    ("Kiosk", "Kiosk"),
    ("Retail", "Retail"),
    )
    name = models.CharField(max_length=100)
    site_code = models.CharField(max_length=100, null=True, blank=True)
    timezone = models.CharField(choices=TIMEZONE_CHOICES, default="CST", max_length=10)
    site_type = models.CharField(choices=SITE_TYPE_CHOICES, default="Datacenter", max_length=20)
    address = models.CharField(max_length=100)
    city = models.CharField(max_length=100)
    zip = models.IntegerField()
    state = models.CharField(max_length=100)
    poc_name = models.CharField(max_length=100)
    poc_number = models.CharField(max_length=100)
    notes = models.TextField(null=True, blank=True)
    def __str__(self):
        return str(self.name)
    
class Platform(models.Model):
    class Meta:
        ordering = ['manufacturer']
    NETMIKO_CHOICES = (
    ("alcatel_sros", "alcatel_sros"),
    ("arista_eos", "arista_eos"),
    ("aruba_osswitch", "aruba_osswitch"),
    ("aruba_aoscx", "aruba_aoscx"),
    ("cisco_asa", "cisco_asa"),
    ("cisco_ftd", "cisco_ftd"),
    ("cisco_ios", "cisco_ios"),
    ("cisco_nxos", "cisco_nxos"),
    ("cisco_wlc", "cisco_wlc"),
    ("cisco_xe", "cisco_xe"),
    ("f5_tmsh", "f5_tmsh"),
    ("f5_linux", "f5_linux"),
    ("huawei", "huawei"),
    ("juniper_junos", "juniper_junos"),
    ("juniper_screenos", "juniper_screenos"),
    ("linux", "linux"),
    ("nokia_sros", "nokia_sros"),
    ("nokia_srl", "nokia_srl"),
    ("paloalto_panos", "paloalto_panos"),
    )
    ANSIBLE_CHOICES = (
    ("ansible.netcommon.network_cli", "ansible.netcommon.network_cli"),
    ("arista.eos.eos", "arista.eos.eos"),
    ("arubanetworks.aoscx.aoscx", "arubanetworks.aoscx.aoscx"),
    ("cisco.asa.asa", "cisco.asa.asa"),
    ("cisco.ios.ios", "cisco.ios.ios"),
    ("cisco.nxos.nxos", "cisco.nxos.nxos"),
    ("cisco.iosxr.iosxr", "cisco.iosxr.iosxr"),
    ("f5networks.f5_modules", "f5networks.f5_modules"),
    ("junipernetworks.junos.junos", "junipernetworks.junos.junos"),
    ("fortinet.fortios.fortios", "fortinet.fortios.fortios"),
    ("nokia.sros.sros", "nokia.sros.sros"),
    ("paloaltonetworks.panos", "paloaltonetworks.panos"),
    )
    NAPALM_CHOICES = (
    ("eos", "eos"),
    ("ios", "ios"),
    ("iosxr", "iosxr"),
    ("iosxr_netconf", "iosxr_netconf"),
    ("junos", "junos"),
    ("nxos", "nxos"),
    ("nxos_ssh", "nxos_ssh"),
    ("napalm_aos", "napalm_aos"),
    ("napalm_aoscx", "napalm_aoscx"),
    ("napalm_ciena-saos", "napalm_ciena-saos"),
    ("napalm_fortios", "napalm_fortios"),
    ("napalm_panos", "napalm_panos"),
    ("napalm_srlinux", "napalm_srlinux"),
    )
    STATUS_CHOICES = (
    ("Active", "Active"),
    ("Deprecated", "Deprecated"),
    ("End of Life", "End of Life"),
    )
    FORM_FACTOR_CHOICES = (
    ("Appliance", "Appliance"),
    ("Blade/Module", "Blade/Module"),
    ("Rack", "Rack"),
    ("Virtual", "Virtual"),
    )
    manufacturer = models.CharField(max_length=100)
    name = models.CharField(max_length=100)
    PID = models.CharField(max_length=100)
    status = models.CharField(choices=STATUS_CHOICES, default="Active", max_length=100)
    eol_date = models.DateField(null=True, blank=True)
    form_factor = models.CharField(choices=FORM_FACTOR_CHOICES, default="Active", max_length=100)
    ansible_namespace = models.CharField(choices=ANSIBLE_CHOICES, default="", max_length=100, blank=True)
    netmiko_namespace = models.CharField(choices=NETMIKO_CHOICES, default="", max_length=100, blank=True)
    napalm_namespace = models.CharField(choices=NAPALM_CHOICES, default="", max_length=100, blank=True)
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
        indexes = [
            models.Index(fields=["site"]),
            models.Index(fields=["platform"]),
            models.Index(fields=["status"]),
            models.Index(fields=["name"]),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["ipaddress_mgmt"], name="uniq_mgmt_ip", condition=~models.Q(ipaddress_mgmt=None)
            ),
            models.UniqueConstraint(
                fields=["serial_number"], name="uniq_serial", condition=~models.Q(serial_number="")
            ),
        ]
    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        STAGING = "staging", "Staging"
        MAINT   = "maintenance", "Maintenance"
        RETIRED = "retired", "Retired"
    # Identity
    name = models.CharField(max_length=100)
    name_lookup = models.CharField(max_length=200, blank=True, default="") # FQDN
    site = models.ForeignKey(Site, null=True, blank=True, on_delete=models.SET_NULL)
    platform = models.ForeignKey(Platform, null=True, blank=True, on_delete=models.SET_NULL)
    serial_number = models.CharField(max_length=50, blank=True, default="")
    # Management
    ipaddress_mgmt = models.GenericIPAddressField(protocol='IPv4', null=True, blank=True)
    ipaddress_rest = models.GenericIPAddressField(protocol='IPv4', null=True, blank=True)
    ipaddress_gnmi = models.GenericIPAddressField(protocol='IPv4', null=True, blank=True)
    port_rest = models.IntegerField(default=443, validators=[MinValueValidator(1), MaxValueValidator(65535)])
    port_netc = models.IntegerField(default=830, validators=[MinValueValidator(1), MaxValueValidator(65535)])
    port_gnmi = models.IntegerField(default=9339, validators=[MinValueValidator(1), MaxValueValidator(65535)])
    # Classification
    status = models.CharField(max_length=24, choices=Status.choices, default=Status.ACTIVE)
    device_tag = models.ManyToManyField(DeviceTag)
    # Authentication
    creds_ssh = models.ForeignKey(NetworkCredential, null=True, on_delete=models.SET_NULL, blank=True, related_name="inventory_creds_ssh")
    creds_rest = models.ForeignKey(NetworkCredential, null=True, on_delete=models.SET_NULL, blank=True, related_name="inventory_creds_rest")
    # Discovery Metadata
    first_seen_at = models.DateTimeField(null=True, blank=True)
    last_seen_at = models.DateTimeField(null=True, blank=True)
    last_audit_at = models.DateTimeField(null=True, blank=True)
    last_backup_at = models.DateTimeField(null=True, blank=True)
    discovery_source = models.CharField(max_length=64, blank=True, default="")
    sw_version = models.CharField(max_length=128, blank=True, default="")
    # Priority/Tracked Interfaces
    priority_interfaces = models.CharField(max_length=750, blank=True)
    def get_priority_interfaces(self):
        return [k.strip() for k in (self.priority_interfaces or "").split(",") if k.strip()]
    def set_priority_interfaces(self, items):
        self.priority_interfaces = ",".join([str(i).strip() for i in (items or [])])
    # Flex Field
    extra = models.JSONField(blank=True, default=dict)

    def save(self, *args, **kwargs):
        # normalize fields
        if self.name_lookup:
            self.name_lookup = self.name_lookup.strip().lower()
        if self.serial_number:
            self.serial_number = self.serial_number.strip().upper()
        # seed first_seen_at
        if not self.pk and not self.first_seen_at:
            self.first_seen_at = timezone.now()
        super().save(*args, **kwargs)

    def __str__(self):
        return str(self.name)
    
class InventoryInterface(models.Model):
    device = models.ForeignKey(Inventory, related_name="interfaces", on_delete=models.CASCADE)
    name = models.CharField(max_length=128)
    is_priority = models.BooleanField(default=False)