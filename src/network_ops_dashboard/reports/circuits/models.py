from __future__ import unicode_literals
from django.db import models
from network_ops_dashboard.inventory.models import Site

# Create your models here.

class CircuitProvider(models.Model):
    class Meta:
        ordering = ['name']

    PROVIDER_CHOICES = [('ATT', 'ATT'), ('Cogent', 'Cogent'), ('GTT', 'GTT'),
                        ('Lumen', 'Lumen'), ('Verizon', 'Verizon'), ('Windstream', 'Windstream'),
                        ('Zayo', 'Zayo')]

    name = models.CharField(max_length=30, choices=PROVIDER_CHOICES, default='ATT', unique=True)
    email_folder = models.TextField()
    function_name = models.CharField(max_length=200, blank=True)

    def save(self, *args, **kwargs):
        if self.name and not self.function_name:
            self.function_name = f"process_{self.name.lower().strip()}"
        super().save(*args, **kwargs)

    def __str__(self):
        return str(self.name)

class CircuitTag(models.Model):
    class Meta:
        ordering = ['name']
    name = models.CharField(max_length=100)

    def __str__(self):
        return str(self.name)

class Circuit(models.Model):
    class Meta:
        ordering = ['name']
    name = models.CharField(max_length=100)
    cktid = models.CharField(max_length=100)
    provider = models.ForeignKey(CircuitProvider, on_delete=models.CASCADE, related_name='circuit_provider_name')
    tag = models.ManyToManyField(CircuitTag)
    site = models.ForeignKey(Site, on_delete=models.SET_NULL, null=True, blank=True, related_name='circuit_site')
    notes = models.TextField(null=True, blank=True)

    def __str__(self):
        return str(self.name)

class CircuitMtcEmail(models.Model):
    class Meta:
        ordering = ['startdatetime']
    mtc_id = models.CharField(max_length=20, unique=True)
    status = models.CharField(max_length=20)
    impact = models.CharField(max_length=100)
    circuits = models.ManyToManyField(Circuit)
    startdatetime = models.CharField(max_length=100)
    enddatetime = models.CharField(max_length=100)

    # Catch-all for anything else
    metadata = models.JSONField(blank=True, null=True)

    def __str__(self):
        strckt = str('')
        for ckt in self.circuits.all():
            if strckt == '':
                strckt = ckt.name
            else:
                strckt = strckt + ', ' + ckt.name
        return str(self.mtc_id) + " - " + strckt