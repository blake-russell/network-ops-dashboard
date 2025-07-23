#!/django/venv/bin/python

from netmiko import ConnectHandler
from netmiko import Netmiko
import logging
from requests.auth import HTTPBasicAuth
from network_ops_dashboard.models import *
from network_ops_dashboard.asavpn.models import *
from network_ops_dashboard.asavpn.scripts.showvpnconnected import *

logger = logging.getLogger('network_ops_dashboard.asavpn')

showVPNconnected()
