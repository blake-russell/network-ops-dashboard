from django import forms
from django.utils.translation import gettext as _
from network_ops_dashboard.models import *
from network_ops_dashboard.notices.certexpiry.models import *
import json

# Create your forms here.

class CertProviderForm(forms.ModelForm):
    class Meta:
        model = CertProvider
        fields = ('name', 'certexpiry_folder')
    PROVIDER_CHOICES = [('Entrust', 'Entrust'), ('Digicert', 'Digicert'), ('Geotrust', 'Geotrust'), \
                    ('Rapidssl', 'Rapidssl'), ('Letsencrypt', 'Letsencrypt'), ('Symantec', 'Symantec'), \
                        ('Comodo', 'Comodo'), ('Securetrust', 'Securetrust')]
    name = forms.ChoiceField(label="Name:", choices=PROVIDER_CHOICES, required=True)
    certexpiry_folder = forms.CharField(label="Email Folder:", help_text="Script will parse emails from this folder", required=True)