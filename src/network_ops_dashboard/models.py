from __future__ import unicode_literals
from django.utils.translation import gettext, gettext_lazy as _
from django_cryptography.fields import encrypt
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