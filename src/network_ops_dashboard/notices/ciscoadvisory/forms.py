from django import forms

class CiscoAdvisoryStatusForm(forms.Form):
    STATUS_CHOICES = [
        ("Impacted", "Impacted"),
        ("No Impact", "No Impact"),
    ]
    status = forms.ChoiceField(choices=STATUS_CHOICES, required=True)
    note = forms.CharField(
        required=True,
        widget=forms.Textarea(attrs={"rows": 4, "class": "form-control"}),
        help_text="Provide reasoning or remediation steps."
    )