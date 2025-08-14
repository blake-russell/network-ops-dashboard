import requests
import logging
from requests.auth import HTTPBasicAuth
from network_ops_dashboard.models import SiteSecrets, NetworkCredential
from network_ops_dashboard.inventory.models import Inventory
from network_ops_dashboard.asavpn.models import AsaVpnConnectedUsers 

logger = logging.getLogger('network_ops_dashboard.asavpn')

def showVPNconnected():
    #urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    headers = {'User-Agent': 'ASDM'}
    try:
        creds_name = SiteSecrets.objects.filter(varname='asavpn_primary_user')[0].varvalue
        creds = NetworkCredential.objects.filter(username_lookup=creds_name)
    except ImportError as e:
        logger.exception(f"No asavpn_primary_user set in SiteSecrets.objects(): {e}")
    auth = HTTPBasicAuth(creds[0].username, creds[0].password)
    baseStr = '/admin/exec/show%20vpn-sessiondb'
    asaInv = Inventory.objects.filter(device_tag__name__exact='ASAVPN') # Update tag name if necessary or remove tags to ignore
    for TargetDevice in asaInv:
        try:
            r = requests.get('https://' + str(TargetDevice) + baseStr, headers=headers, auth=auth, verify=False)
            if r.text != '':
                    try:
                        output1 = r.text.split('AnyConnect Client            :')[-1]
                        output2 = output1.split(':')[0].strip() # Connected User
                        output3 = r.text.split('Device Load                  :')[-1].strip()
                        output4 = output3.split('\n')[0].strip() # Load
                        #save entry to db
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