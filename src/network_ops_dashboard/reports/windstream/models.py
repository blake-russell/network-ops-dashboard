from __future__ import unicode_literals
from django.utils.translation import gettext, gettext_lazy as _
from django_cryptography.fields import encrypt
from django.db import models
from django.conf import settings

# Create your models here.
 
class WindstreamCktID(models.Model):
    class Meta:
        ordering = ['name']
    cktid = models.CharField(max_length=100)
    name = models.CharField(max_length=100)
    def __str__(self):
        return str(self.name)
        
class WindstreamMtcEmail(models.Model):
    class Meta:
        ordering = ['startdatetime']
    wmt = models.IntegerField(unique=True)
    status = models.CharField(max_length=20)
    impact = models.CharField(max_length=100)
    cktid = models.ManyToManyField(WindstreamCktID)
    startdatetime = models.CharField(max_length=100)
    enddatetime = models.CharField(max_length=100)
    def __str__(self):
        strckt = str('')
        for ckt in self.cktid.all():
            if strckt == '':
                strckt = ckt.name
            else:
                strckt = strckt + ', ' + ckt.name
        return str(self.wmt) + " - " + strckt