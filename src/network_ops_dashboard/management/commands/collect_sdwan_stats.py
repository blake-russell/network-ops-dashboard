from django.core.management.base import BaseCommand
from network_ops_dashboard.scripts.cachegate import _cache_gate
import logging
from django.utils import timezone

logger = logging.getLogger(f'{__name__}')

class Command(BaseCommand):
    help = "Collect Cisco SD-WAN path stats for dashboard cards"

    def handle(self, *args, **kwargs):
        from network_ops_dashboard.models import FeatureFlags
        from network_ops_dashboard.sdwan.vmanage.models import SdwanSettings
        from network_ops_dashboard.sdwan.vmanage.scripts.services import VManage

        s = SdwanSettings.load()
        flags = FeatureFlags.load()
        if not s.card_enabled or not flags.enable_sdwan_cards:
            logger.info("SD-WAN: disabled; skipping.")
            return
        if not s.host:
            logger.info("SD-WAN: no host configured; skipping.")
            return

        now = timezone.now()

        gate_key = "sdwan_vmanage_sync_vedge_last"
        if not _cache_gate(gate_key, flags.sdwan_interval_minutes):
            return 0

        logger.info("SD-WAN: stats collection started.")
        
        VManage.CollectVmanageStats(s, flags, now)

        logger.info("SD-WAN: stats collection completed.")