#!/django/venv/bin/python

from netmiko import ConnectHandler
from netmiko import Netmiko
import logging
from requests.auth import HTTPBasicAuth
from network_ops_dashboard.models import *
from network_ops_dashboard.asavpn.models import *
from network_ops_dashboard.asavpn.scripts.showvpnconnected import *

logger = logging.getLogger('network_ops_dashboard.asavpn')

flags = FeatureFlags.load()

# Grab VPN connected stats (In seperate cron folder to trigger at different time.)
if not flags.enable_asa_vpn_stats:
    logger.info("ASAVPN stats collection disabled in FeatureFlags. Enable it and then setup a cronjob to run this script into manage.py.")
    # ie. crontab job below:
    # */5 * * * * /pathto/project_venv/bin/python /pathto/project_venv/src/manage.py shell < /pathto/project_venv/src/network_ops_dashboard/cron/AsaVpnConnectedUsers.py
    # Runs every 5 minutes
    sys.exit(0)
else:
    showVPNconnected()