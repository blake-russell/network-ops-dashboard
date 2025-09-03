from __future__ import unicode_literals
from django.db import models

# Create your models here.
 
class CiscoAdvisory(models.Model):
    STATUS_CHOICES = [('Open', 'Open'), ('Impacted', 'Impacted'), ('No Impact', 'No Impact'), ('Archived', 'Archived')]

    title = models.CharField(max_length=300)
    title_short = models.CharField(max_length=100, unique=True)
    impact_rating = models.CharField(max_length=50)
    description = models.TextField()
    url = models.TextField(blank=True)
    date = models.DateField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='Open')
    note = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title_short}"