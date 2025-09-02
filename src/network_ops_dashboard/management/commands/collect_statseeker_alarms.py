from django.core.management.base import BaseCommand
from network_ops_dashboard.scripts.cachegate import _cache_gate
import logging

logger = logging.getLogger(f'{__name__}')

class Command(BaseCommand):
    help = "Collect Statseeker Alarms."

    def handle(self, *args, **kwargs):
        from network_ops_dashboard.models import FeatureFlags
        from network_ops_dashboard.notices.statseeker.models import StatseekerSettings
        from network_ops_dashboard.notices.statseeker.scripts.services import statseeker_sync_alerts

        cfg = StatseekerSettings.load()
        flags = FeatureFlags.load()
        if not cfg.enabled or not flags.enable_statseeker_alarms:
            logger.info("Statseeker: disabled; skipping.")
            return
        if not cfg.credential or not cfg.base_url:
            logger.info("Statseeker: no key or url configured; skipping.")
            return

        gate_key = "statseeker_sync_alerts_last"
        if not _cache_gate(gate_key, cfg.min_interval_minutes):
            return 0

        logger.info("Statseeker: collection started.")
        statseeker = statseeker_sync_alerts()
        try:
            logger.info(f"Statseeker: collection completed. {statseeker['created']} created, {statseeker['updated']} updated, {statseeker['resolved']} resolved, {statseeker['processed']} objects processed.")
        except Exception as e:
            logger.info("Statseeker: collection completed. Error processing stats: %s." %e)