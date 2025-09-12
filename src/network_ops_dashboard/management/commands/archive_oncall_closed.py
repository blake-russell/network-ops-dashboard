from django.core.management.base import BaseCommand
from django.utils import timezone
import logging
from network_ops_dashboard.oncall.models import OnCallIncident, OnCallSettings
from network_ops_dashboard.notices.ciscoadvisory.models import CiscoAdvisory

logger = logging.getLogger(f'network_ops_dashboard.{__name__}')

class Command(BaseCommand):
    help = "Archive all Closed on-call incidents & Cisco Field Notices (move to Archived)."

    def handle(self, *args, **kwargs):
        settings_obj = OnCallSettings.load()
        if not settings_obj.auto_archive_enabled:
            logger.info("On-call Archiving is disabled.")
            return
        # On-Call Incidents
        incident_qs = OnCallIncident.objects.filter(status="Closed")
        now = timezone.now()
        inc_count = 0
        logger.info("On-call Archiving Started.")
        for inc in incident_qs:
            inc.status = "Archived"
            inc.date_archived = now
            inc.save(update_fields=["status", "date_archived"])
            inc_count += 1
        logger.info(f"On-Call archived {inc_count} incident(s).")
        # Cisco Field Notices
        ciscoadvisory_qs = CiscoAdvisory.objects.filter(status='No Impact')
        fn_count = 0
        logger.info("CiscoAdvisory Archiving Started.")
        for fn in ciscoadvisory_qs:
            fn.status = "Archived"
            fn.save(update_fields=["status"])
            fn_count += 1
        logger.info(f"CiscoAdvisory archived {fn_count} field notice(s).")