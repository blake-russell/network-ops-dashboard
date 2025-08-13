import logging
from django.core.management.base import BaseCommand
from django.utils import timezone

logger = logging.getLogger(f'network_ops_dashboard.{__name__}')

class Command(BaseCommand):
    help = "Collect ASA VPN stats into AsaVpnConnectedUsers"

    def handle(self, *args, **kwargs):
        from network_ops_dashboard.models import FeatureFlags
        from network_ops_dashboard.asavpn.scripts.showvpnconnected import showVPNconnected

        flags = FeatureFlags.load()
        if not flags.enable_asa_vpn_stats:
            logger.info("ASA VPN stats collection disabled. Exiting.")
            return

        now = timezone.now()
        last = flags.asa_vpn_last_run
        interval = max(flags.asa_vpn_interval_minutes, 1)

        if last and (now - last).total_seconds() < interval * 60:
            return
        
        logger.info("ASA VPN stats collection started.")

        showVPNconnected()

        flags.asa_vpn_last_run = now
        flags.save(update_fields=["asa_vpn_last_run", "updated_at"])
        logger.info("ASA VPN stats collection completed.")