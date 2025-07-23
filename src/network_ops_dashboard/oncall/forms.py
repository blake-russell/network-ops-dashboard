from django import forms
from django.utils.translation import gettext as _
from django.db import models
from network_ops_dashboard.models import *
from network_ops_dashboard.inventory.models import *
from network_ops_dashboard.oncall.models import *
import json

# Create your forms here.

class OnCallIncidentForm(forms.ModelForm):
    class Meta:
        model = OnCallIncident
        fields = ['headline', 'log']
    
    headline = forms.CharField(widget=forms.Textarea(attrs={'rows': 1, 'cols': 40}),label="Issue Title")
    log = forms.CharField(widget=forms.Textarea(attrs={'rows': 5, 'cols': 40}),label="Issue Details")

    def clean_title(self):
        return self.cleaned_data['headline']