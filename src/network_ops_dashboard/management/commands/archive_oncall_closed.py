from django.core.management.base import BaseCommand
from django.utils import timezone
import logging
from network_ops_dashboard.oncall.models import OnCallIncident, OnCallSettings

logger = logging.getLogger(f'network_ops_dashboard.{__name__}')

class Command(BaseCommand):
    help = "Archive all Closed on-call incidents (move to Archived)."

    def handle(self, *args, **kwargs):
        settings_obj = OnCallSettings.load()
        if not settings_obj.auto_archive_enabled:
            logger.info("On-call Archiving is disabled.")
            return
        qs = OnCallIncident.objects.filter(status="Closed")
        now = timezone.now()
        count = 0
        logger.info("On-call Archiving Started.")
        for inc in qs:
            inc.status = "Archived"
            inc.date_archived = now
            inc.save(update_fields=["status", "date_archived"])
            count += 1
        logger.info(f"On-Call archived {count} incident(s).")