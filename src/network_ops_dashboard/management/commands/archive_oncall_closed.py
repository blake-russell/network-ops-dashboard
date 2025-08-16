from django.core.management.base import BaseCommand
from django.utils import timezone
from network_ops_dashboard.oncall.models import OnCallIncident, OnCallSettings

class Command(BaseCommand):
    help = "Archive all Closed on-call incidents (move to Archived)."

    def handle(self, *args, **kwargs):
        settings_obj = OnCallSettings.load()
        if not settings_obj.auto_archive_enabled:
            return
        qs = OnCallIncident.objects.filter(status="Closed")
        now = timezone.now()
        count = 0
        for inc in qs:
            inc.status = "Archived"
            inc.date_archived = now
            inc.save(update_fields=["status", "date_archived"])
            count += 1
        self.stdout.write(self.style.SUCCESS(f"Archived {count} incident(s)."))