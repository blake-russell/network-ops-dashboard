from __future__ import unicode_literals
from django.utils.translation import gettext, gettext_lazy as _
from django_cryptography.fields import encrypt
from django.db import models
from django.conf import settings
from django.utils import timezone
from django.core.validators import MinValueValidator
from network_ops_dashboard.inventory.models import Site

# Create your models here.
 
class CompanyChanges(models.Model):
    team_name = models.CharField(max_length=100)
    change_id = models.CharField(max_length=100, unique=True)
    scheduled_start = models.DateTimeField()
    scheduled_end = models.DateTimeField()
    location = models.CharField(max_length=100)
    summary = models.TextField()

    # Optional fields
    class_type = models.CharField(max_length=100, blank=True, null=True) 
    risk = models.CharField(max_length=100, blank=True, null=True)
    group = models.CharField(max_length=100, blank=True, null=True)
    manager = models.CharField(max_length=100, blank=True, null=True)

    # Catch-all for anything else
    metadata = models.JSONField(blank=True, null=True)

    imported_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.change_id}_({self.team_name})"
    
class CompanyChangesSettings(models.Model):
    changes_folder = models.CharField(max_length=500, help_text="Folder containing .msg files")
    extract_folder = models.CharField(max_length=500, help_text="Folder to write extracted .xlsx")

    # Excel parsing knobs
    header_row = models.PositiveIntegerField(default=4, validators=[MinValueValidator(1)],
        help_text="1-based row number where the header line lives (e.g., 4 for 'skiprows=3')")
    days_before = models.PositiveIntegerField(default=1, validators=[MinValueValidator(1)],
        help_text="Include changes scheduled within N days from before today")
    days_ahead = models.PositiveIntegerField(default=7, validators=[MinValueValidator(1)],
        help_text="Include changes scheduled within N days from today")

    # Site Validator
    use_sites_for_locations = models.BooleanField(default=True)
    sites_to_filter = models.ManyToManyField(
        Site,
        blank=True,
        related_name="change_filter_sets",
        help_text="If any sites are selected here, only these site names will be used as valid locations."
    )
    custom_valid_locations = models.JSONField(default=list, blank=True)

    # Map Excel column headers -> internal fields (unknown keys land in metadata)
    # Example:
    # {
    #   "team_name": "Team Name",
    #   "change_id": "Change#",
    #   "scheduled_start": "Scheduled Start",
    #   "scheduled_end": "Scheduled End",
    #   "location": "Location",
    #   "summary": "Change Description",
    #   "reason": "Change Reason",
    #   "risk": "Risk Level",
    #   "group": "Assignment Group",
    #   "class_type": "Change Class"
    # }
    column_map = models.JSONField(default=dict, blank=True)

    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return "Company Changes Settings"

    class Meta:
        verbose_name = "Company Changes Settings"
        verbose_name_plural = "Company Changes Settings"