from django.core.management.base import BaseCommand
from network_ops_dashboard.scripts.cachegate import _cache_gate
import logging

logger = logging.getLogger(f'{__name__}')

class Command(BaseCommand):
    help = "Collect ASA VPN stats into AsaVpnConnectedUsers"

    def handle(self, *args, **kwargs):
        from network_ops_dashboard.models import FeatureFlags
        from network_ops_dashboard.asavpn.scripts.showvpnconnected import showVPNconnected

        flags = FeatureFlags.load()
        if not flags.enable_asa_vpn_stats:
            logger.info("ASA VPN stats collection disabled. Exiting.")
            return

        gate_key = "asavpn_sync_stats_last"
        if not _cache_gate(gate_key, flags.asa_vpn_interval_minutes):
            return 0
        
        logger.info("ASA VPN stats collection started.")

        showVPNconnected()

        logger.info("ASA VPN stats collection completed.")