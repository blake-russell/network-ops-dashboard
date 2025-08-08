from django import forms
from network_ops_dashboard.models import *
from network_ops_dashboard.reports.circuits.models import *
from network_ops_dashboard.inventory.models import Site

# Create your forms here.

class CircuitProviderForm(forms.ModelForm):
    class Meta:
        model = CircuitProvider
        fields = ('name', 'email_folder')
    PROVIDER_CHOICES = [('ATT', 'ATT'), ('Cogent', 'Cogent'), ('GTT', 'GTT'),
                        ('Lumen', 'Lumen'), ('Verizon', 'Verizon'), ('Windstream', 'Windstream'),
                        ('Zayo', 'Zayo')]
    name = forms.ChoiceField(label="Provider:", choices=PROVIDER_CHOICES, required=True)
    email_folder = forms.CharField(label="Email Folder:", help_text="Script will parse emails from this folder", required=True)

class CircuitTagForm(forms.ModelForm):
    class Meta:
        model = CircuitTag
        fields = ('name',)
    name = forms.CharField(label="Circuit Tag:", required=True)

class CircuitForm(forms.ModelForm):
    class Meta:
        model = Circuit
        fields = ('name', 'cktid', 'provider', 'site', 'tag', 'notes')
    name = forms.CharField(label="Circuit Name:", help_text="ie: Dallas Core Primary", required=True)
    cktid = forms.CharField(label="Circuit ID/#:", required=True)
    provider = forms.ModelChoiceField(label="Provider:", queryset=CircuitProvider.objects.all(), required=True)
    site = forms.ModelChoiceField(label="Site:", queryset=Site.objects.all(), required=False)
    tag = forms.ModelMultipleChoiceField(label="Tags:", queryset=CircuitTag.objects.all(), widget=forms.SelectMultiple(attrs={'class': 'form-select', 'size': '10'}), required=False)
    notes = forms.TextInput()