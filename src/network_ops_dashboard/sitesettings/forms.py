from django import forms
from django.utils.translation import gettext as _
from network_ops_dashboard.models import *

# Create your forms here.

class SiteSettingsForm(forms.ModelForm):
    class Meta:
        model = SiteSettings
        fields = ('company', 'teamname', 'websites', 'publicscripts', 'companylogo')
    company = forms.CharField(label="Company Name:", required=True)
    teamname = forms.CharField(label="Team Name:", required=True)
    websites = forms.ModelMultipleChoiceField(label="Home Site Websites:", help_text="Websites show up on main public page.", queryset=SiteSettingsWebsite.objects.all(), widget=forms.SelectMultiple(attrs={'class': 'form-select'}), required=False)
    publicscripts = forms.ModelMultipleChoiceField(label="Public Script Page Websites:", help_text="Websites show up public scripts page.", queryset=SiteSettingsWebsite.objects.all(), widget=forms.SelectMultiple(attrs={'class': 'form-select'}), required=False)
    companylogo = forms.ImageField()

class SiteSettingsWebsiteForm(forms.ModelForm):
    class Meta:
        model = SiteSettingsWebsite
        fields = ('name', 'url')
    name = forms.CharField(label="Site Text:", required=True)
    url = forms.CharField(label="Site URL:", required=True)

class SiteSecretsForm(forms.ModelForm):
    class Meta:
        model = SiteSecrets
        fields = ('varname', 'varvalue')
    varname = forms.CharField(label="Var Name:", required=True)
    widgets = {
            'varvalue': forms.Textarea(attrs={'rows': 10, 'cols': 40}),
        }