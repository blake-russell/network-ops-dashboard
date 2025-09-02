from django.core.management.base import BaseCommand
from network_ops_dashboard.scripts.cachegate import _cache_gate
import logging

logger = logging.getLogger(f'{__name__}')

class Command(BaseCommand):
    help = "Collect Open PagerDuty Incidents."

    def handle(self, *args, **kwargs):
        from network_ops_dashboard.models import FeatureFlags
        from network_ops_dashboard.notices.pagerduty.models import PagerDutySettings
        from network_ops_dashboard.notices.pagerduty.scripts.services import pd_sync_open_incidents as collected_ids

        cfg = PagerDutySettings.load()
        flags = FeatureFlags.load()
        if not cfg.enabled or not flags.enable_pd_alarms:
            logger.info("PagerDuty: disabled; skipping.")
            return
        if not cfg.credential:
            logger.info("PagerDuty: no key configured; skipping.")
            return

        cache_key = "pd_sync_open_incidents_last"
        if not _cache_gate(cache_key, cfg.min_interval_minutes):
            return 0

        logger.info("PagerDuty: collection started.")
        logger.info(f"PagerDuty: collection of {collected_ids()} incidents completed.")