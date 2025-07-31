from __future__ import unicode_literals
from django.utils.translation import gettext, gettext_lazy as _
from django_cryptography.fields import encrypt
from django.db import models
from django.conf import settings
from django.utils import timezone

# Create your models here.

class CertProvider(models.Model):
    PROVIDER_CHOICES = [('Entrust', 'Entrust'), ('Digicert', 'Digicert'), ('Geotrust', 'Geotrust'), \
                        ('Rapidssl', 'Rapidssl'), ('Letsencrypt', 'Letsencrypt'), ('Symantec', 'Symantec'), \
                            ('Comodo', 'Comodo'), ('Securetrust', 'Securetrust')]

    name = models.CharField(max_length=30, choices=PROVIDER_CHOICES, default='Entrust', unique=True)
    certexpiry_folder = models.TextField()
    function_name = models.CharField(max_length=200, blank=True)

    def save(self, *args, **kwargs):
        if self.name and not self.function_name:
            self.function_name = f"process_{self.name.lower().strip()}"
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.name}"

class CertExpiry(models.Model):
    STATUS_CHOICES = [('Open', 'Open'), ('Closed', 'Closed')]

    provider = models.ForeignKey(CertProvider, on_delete=models.CASCADE, related_name='cert_provider_name')
    cert_name = models.CharField(max_length=200, unique=True)
    common_name = models.CharField(max_length=200)
    expire_date = models.DateField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='Open')
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.provider}_{self.cert_name}"
    
