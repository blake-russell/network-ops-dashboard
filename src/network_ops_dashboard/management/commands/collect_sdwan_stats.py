from django.core.management.base import BaseCommand
from django.core.cache import cache
from django.utils import timezone
import logging

logger = logging.getLogger('network_ops_dashboard.sdwan.vmanage')

class Command(BaseCommand):
    help = "Collect Cisco SD-WAN path stats for dashboard cards"

    def handle(self, *args, **kwargs):
        from network_ops_dashboard.models import FeatureFlags
        from network_ops_dashboard.sdwan.vmanage.models import SdwanSettings
        from network_ops_dashboard.sdwan.vmanage.scripts.services import VManage

        s = SdwanSettings.load()
        flags = FeatureFlags.load()
        if not s.card_enabled and flags.enable_sdwan_cards:
            logger.info("SD-WAN: disabled; skipping.")
            return
        if not s.host:
            logger.info("SD-WAN: no host configured; skipping.")
            return

        now = timezone.now()
        last = flags.sdwan_stats_last_run
        interval = max(flags.sdwan_interval_minutes, 1)

        if last and (now - last).total_seconds() < interval * 60:
            return

        logger.info("SD-WAN: stats collection started.")
        
        VManage.CollectVmanageStats(s, flags, now)

        flags.sdwan_stats_last_run = now
        flags.save(update_fields=["sdwan_stats_last_run"])
        logger.info("SD-WAN: stats collection completed.")