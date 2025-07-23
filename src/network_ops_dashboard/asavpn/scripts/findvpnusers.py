from netmiko import ConnectHandler
from netmiko import Netmiko
import requests
import logging
from requests.auth import HTTPBasicAuth
from network_ops_dashboard.models import *
from network_ops_dashboard.inventory.models import *
from network_ops_dashboard.asavpn.models import *

logger = logging.getLogger('network_ops_dashboard.asavpn')

def findVPNuser(targetUser, username1, password1, targetAction):
    #urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    logger.info(f"findVPNuser Running.")
    headers = {'User-Agent': 'ASDM'}
    try:
        creds_name = SiteSecrets.objects.filter(varname='asavpn_primary_user')[0].varvalue
        creds = NetworkCredential.objects.filter(username_lookup=creds_name)
    except Exception as e:
        logger.exception(f"No asavpn_primary_user set in SiteSecrets.objects(): {e}")
    auth = HTTPBasicAuth(creds[0].username, creds[0].password)
    baseStr = '/admin/exec/show%20vpn-sessiondb%20anyconnect%20%7C%20i%20'
    asaInv = Inventory.objects.filter(device_tag__name__exact='ASAVPN')
    for TargetDevice in asaInv:
        try:
            r1 = requests.get('https://' + str(TargetDevice) + baseStr + targetUser.upper(), headers=headers, auth=auth, verify=False)
            r2 = requests.get('https://' + str(TargetDevice) + baseStr + targetUser.lower(), headers=headers, auth=auth, verify=False)
            targetUsers = r1.text or r2.text
            if targetUsers != '':
                targetUserGrep = targetUsers.split(':')[1].strip().split(' ')[0]
                if targetAction == 'True':
                    target = {
                        'device_type': str(TargetDevice.platform.netmiko_namespace),
	                    'ip': str(TargetDevice),
	                    'username': username1,
	                    'password': password1,
	                    'secret': password1,
	                    'fast_cli': False,
	                    }
                    try:
                        net_conn = ConnectHandler(**target) 
                        Prompt = net_conn.find_prompt()
                        findString = "show vpn-sessiondb anyconnect | i %s" %(targetUserGrep)
                        output1 = net_conn.send_command(findString)
                        if output1 != '':
                            discoAction = "vpn-sessiondb logoff name %s" %(targetUserGrep)
                            output4 = net_conn.send_command(
                                command_string=discoAction,
                                expect_string=r"confirm",
                                strip_prompt=False,
                                strip_command=False,
                            )
                            output4 += net_conn.send_command(
                                command_string="\n",
                                expect_string=r"#",
                                strip_prompt=False,
                                strip_command=False,
                            )
                            discoUserLog = str(net_conn.send_command("show clock")).replace('\n', '') + " - %s disconnected from %s" %(targetUserGrep,TargetDevice)
                            log_entry = AsaVpnDiscoLog.objects.create(username=str(username1),logoutput=str(discoUserLog))
                            log_entry.save()
                            net_conn.disconnect()
                            logger.info(f"findVPNuser disconnected user {targetUserGrep}.")
                            return discoUserLog
                        else:
                            net_conn.disconnect()
                            logger.info(f"findVPNuser issue disconnecting user {targetUserGrep}.")
                            return 'Issue disconnecting %s on %s' %(targetUserGrep,TargetDevice)
                    except Exception as e:
                        return 'Exception @ inner try...%s' %(e)
                else:
                    return "To manually force user logoff enter this command on %s...'vpn-sessiondb logoff name %s'" %(TargetDevice,targetUserGrep)
            else:
                continue
        except Exception as e:
            logger.exception(f"findVPNuser exception @ outer try. ({e})")
            return 'Exception @ outer try...%s' %(e)
    if targetUsers == '':
        return 'No matches found on that LANDID: %s' %(targetUser)