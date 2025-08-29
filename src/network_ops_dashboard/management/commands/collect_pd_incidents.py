from django.core.management.base import BaseCommand
from django.core.cache import cache
from django.utils import timezone
import logging

logger = logging.getLogger('network_ops_dashboard.notices.pagerduty')

def _cache_gate(key: str, minutes: int) -> bool:
    now = timezone.now()
    ttl = minutes * 60

    lock_key = f"{key}_lock"
    got_lock = cache.add(lock_key, now.isoformat(), ttl)
    if not got_lock:
        return False

    last = cache.get(key)
    if not last or (now - last).total_seconds() >= ttl:
        cache.set(key, now, ttl)
        return True

    return False

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