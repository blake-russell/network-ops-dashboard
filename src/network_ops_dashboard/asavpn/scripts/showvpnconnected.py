import requests
import logging
from requests.auth import HTTPBasicAuth
from network_ops_dashboard.inventory.models import Inventory
from network_ops_dashboard.asavpn.models import AsaVpnConnectedUsers, AsaVpnSettings

logger = logging.getLogger('network_ops_dashboard.asavpn')

def showVPNconnected():
    #urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    headers = {'User-Agent': 'ASDM'}
    baseStr = '/admin/exec/show%20vpn-sessiondb'
    asa_settings = AsaVpnSettings.load()
    asaInv = Inventory.objects.filter(device_tag__name__exact=asa_settings.device_tag.name)
    for TargetDevice in asaInv:
        try:
            auth = HTTPBasicAuth(TargetDevice.creds_rest.username, TargetDevice.creds_rest.password)
            r = requests.get('https://' + str(TargetDevice) + baseStr, headers=headers, auth=auth, verify=asa_settings.verify_ssl)
            if r.text != '':
                    try:
                        output1 = r.text.split('AnyConnect Client            :')[-1]
                        output2 = output1.split(':')[0].strip() # Connected User
                        output3 = r.text.split('Device Load                  :')[-1].strip()
                        output4 = output3.split('\n')[0].strip() # Load
                        # sanitize
                        if output2 and output4 == 'No sessions to display.':
                            output2 = '0'
                            output4 = '0%'
                        # save entry to db
                        AsaStatEntry_qs = AsaVpnConnectedUsers.objects.filter(name=str(TargetDevice))
                        if AsaStatEntry_qs.exists():
                            AsaStatEntry = AsaStatEntry_qs.first()
                            AsaStatEntry.connected = output2
                            AsaStatEntry.load = output4
                            AsaStatEntry.save()
                    except Exception as e:
                        logger.exception(f"showVPNconnect error @ inner try as: {e}")
            else:
                continue
        except Exception as e:
            logger.exception(f"showVPNconnect error @ outer try as: {e}")
            AsaStatEntry_qs = AsaVpnConnectedUsers.objects.filter(name=str(TargetDevice))
            if AsaStatEntry_qs.exists():
                AsaStatEntry = AsaStatEntry_qs.first()
                AsaStatEntry.connected = 'Could not read/connect.'
                AsaStatEntry.load = 'Could not read/connect.'
                AsaStatEntry.save()
            continue