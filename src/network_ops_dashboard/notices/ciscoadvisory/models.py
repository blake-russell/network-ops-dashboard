from __future__ import unicode_literals
from django.utils.translation import gettext, gettext_lazy as _
from django_cryptography.fields import encrypt
from django.db import models
from django.conf import settings
from django.utils import timezone

# Create your models here.
 
class CiscoAdvisory(models.Model):
    STATUS_CHOICES = [('Open', 'Open'), ('Closed', 'Closed')]

    title = models.CharField(max_length=300)
    title_short = models.CharField(max_length=100, unique=True)
    impact_rating = models.CharField(max_length=50)
    description = models.TextField()
    url = models.TextField(blank=True)
    date = models.DateField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='Open')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title_short}"