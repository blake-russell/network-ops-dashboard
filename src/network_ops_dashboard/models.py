from __future__ import unicode_literals
from django.utils.translation import gettext, gettext_lazy as _
from django_cryptography.fields import encrypt
from django.core.validators import MaxValueValidator
from django.db import models
from django.conf import settings

# Create your models here.
    
class NetworkCredential(models.Model):
    class Meta:
        ordering = ['username_lookup']
    username = encrypt(models.CharField(max_length=100))
    password = encrypt(models.CharField(max_length=100))
    username_lookup = models.CharField(max_length=100, blank=True)
    def save(self, *args, **kwargs):
        self.username_lookup = self.username
        super().save(*args, **kwargs)
    def __str__(self):
        return str(self.username_lookup)
    
class SiteSettingsWebsite(models.Model):
    class Meta:
        ordering = ['name']
    name = models.CharField(max_length=100)
    url = models.CharField(max_length=300)
    def __str__(self):
        return str(self.name)
    
class SiteSettings(models.Model):
    class Meta:
        ordering = ['company']
    def image_file_path(instance, filename):
        # file will be uploaded to MEDIA_ROOT/images/<filename>
        return f'images/{filename}'
    company = models.CharField(max_length=100)
    teamname = models.CharField(max_length=100)
    websites = models.ManyToManyField(SiteSettingsWebsite, related_name='site_websites', blank=True)
    publicscripts = models.ManyToManyField(SiteSettingsWebsite, related_name='public_scripts', blank=True)
    companylogo = models.ImageField(upload_to=image_file_path, blank=True, null=True)
    def __str__(self):
        return str(self.company + ' - ' + self.teamname)
    
class SiteSecrets(models.Model):
    class Meta:
        ordering = ['varname']
    varname = models.CharField(max_length=100)
    varvalue = models.TextField()
    def __str__(self):
        return str(self.varname)
    
class DashboardPrefs(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    layout = models.JSONField(default=dict)

    def enabled_order(self, all_cards):
        order = self.layout.get("order") or [c["id"] for c in all_cards]
        hidden = set(self.layout.get("hidden") or [])
        return [cid for cid in order if cid in {c["id"] for c in all_cards} and cid not in hidden]
    
class FeatureFlags(models.Model):
    enable_asa_vpn_stats = models.BooleanField(default=False)
    asa_vpn_interval_minutes = models.PositiveIntegerField(default=5, validators=[MaxValueValidator(60)])
    asa_vpn_last_run = models.DateTimeField(null=True, blank=True)
    enable_email_processing = models.BooleanField(default=False)
    email_processing_time = models.CharField(max_length=5, default="06:30")
    enable_oncall_email = models.BooleanField(default=False)
    oncall_email_to = models.TextField(blank=True, default="")
    oncall_email_time = models.TimeField(null=True, blank=True)

    # Add new feature settings or features to enable

    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    updated_at = models.DateTimeField(auto_now=True)

    @classmethod
    def load(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj
    
    def __str__(self):
        return "Feature Flags"