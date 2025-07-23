from __future__ import unicode_literals
from django.utils.translation import gettext, gettext_lazy as _
from django_cryptography.fields import encrypt
from django.db import models
from django.conf import settings

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