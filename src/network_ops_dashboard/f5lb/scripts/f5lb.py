import logging
from network_ops_dashboard.models import *
from network_ops_dashboard.inventory.models import *
from network_ops_dashboard.f5lb.models import *
from network_ops_dashboard.f5lb.scripts.f5lb import *
from bigrest.bigip import BIGIP
#BIP-IP Version 16.1.4.1 - Build 0.50.5

logger = logging.getLogger('network_ops_dashboard.f5lb')

# ### Check if LB is active - return True or False
def f5lbCheckActiveState(lb, device):
    trafficgroup = device.load("/mgmt/tm/cm/traffic-group/stats")
    cleanedKey = f'https://localhost/mgmt/tm/cm/traffic-group/~Common~traffic-group-1:~Common~{lb}.uscc.com/stats'
    tgStatus = trafficgroup.properties['entries'][cleanedKey]['nestedStats']['entries']['failoverState']['description']
    if tgStatus == 'active':
        return True
    else:
        return False

### Validate if virtual server exists - return True or False
def f5lbValidateServerExists(targetServer, device):
    if device.exist(f'/mgmt/tm/ltm/virtual/{targetServer}'):
        return True
    else:
        return False

### Validate if ssl profile exists - return True or False as well as currently configured cert/key entry if True
def f5lbSSLProfileExists(targetProfile, device):
    if device.exist(f'/mgmt/tm/ltm/profile/client-ssl/{targetProfile}'):
        sslprofile = device.load(f'/mgmt/tm/ltm/profile/client-ssl/{targetProfile}')
        targetProfileOldCert = sslprofile.properties['cert']
        targetProfileOldCertRef = sslprofile.properties['certReference']['link']
        targetProfileOldKey = sslprofile.properties['key']
        targetProfileOldKeyRef = sslprofile.properties['keyReference']['link']
        return (True, targetProfileOldCert, targetProfileOldCertRef, targetProfileOldKey, targetProfileOldKeyRef)
    else:
        return (False, False)