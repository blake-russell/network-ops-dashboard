import requests
import logging
import json
from collections.abc import Iterable
from django.db.models.query import QuerySet
from network_ops_dashboard.models import *
from network_ops_dashboard.inventory.models import *
from network_ops_dashboard.apic.models import *
from network_ops_dashboard.apic.scripts.apic import apicCookie

logger = logging.getLogger('network_ops_dashboard.apic')

# Inputs from apic_loadconfigoptions view

# Load interface profiles and interface group policies into local database for create interface mop
def LoadAPICConfigListOptions(deviceList, reqUser, theme, creds, creds2):
    try:
        backLink = SiteSecrets.objects.filter(varname='backLink_apic_createinterface')[0].varvalue
    except ImportError:
        backLink = '#'
    # Build StreamingHTTPresponse page
    yield "<html><head><title>APIC Loading Config Options into DB</title>\n"
    yield "<link rel='stylesheet' href='/static/css/base.css'>\n"
    yield "<link rel='stylesheet' href='/static/css/style.css'>\n"
    if theme == 'themelight':
        yield "<link rel='stylesheet' href='https://bootswatch.com/5/lumen/bootstrap.css'></head>\n"
    else:
        yield "<link rel='stylesheet' href='https://bootswatch.com/5/cyborg/bootstrap.css'></head>\n"
    yield "<script src='https://bootswatch.com/_vendor/jquery/dist/jquery.min.js'></script>\n"
    yield "<script src='https://bootswatch.com/_vendor/bootstrap/dist/js/bootstrap.bundle.min.js'></script>\n"
    yield "<hr>"
    yield '<div id="out" style="overflow:auto;">'
    # Testing javascript scrolling
    yield '<script>var out = document.getElementById("out");out.scrollTop = out.scrollHeight - out.clientHeight;</script>'
    # Log Event
    logger.info('APIC LoadAPICConfigListOptions initialized by %s' %(reqUser))
    # Start of Script Logic
    try:
        yield " " * 1024  # Encourage browser to render incrementally
        if not isinstance(deviceList, (list, QuerySet)):
            deviceList = [deviceList]
        for targetDevice in deviceList:
            try:
                apic_lab_devicecheck = json.loads(SiteSecrets.objects.filter(varname='apic_lab_devicecheck')[0].varvalue)
                if any(check in targetDevice.device.name for check in apic_lab_devicecheck):
                    username = creds2[0].username
                    password = creds2[0].password
                else:
                    username = creds[0].username
                    password = creds[0].password
            except Exception:
                # Maybe apic_lab_devicecheck is empty so continue with normal creds
                username = creds[0].username
                password = creds[0].password
                continue
            # Get the Interface Profiles
            try:
                yield 'Gathering interface profiles on  %s.<br>' % (targetDevice.device.name)
                intf_ipfs = []
                aci_token = apicCookie(targetDevice.device.ipaddress_mgmt, username, password)
                headers = {'Content-Type': 'application/json', 'Cookie': f'APIC-Cookie='+aci_token}
                r = requests.get(f'https://{targetDevice.device.ipaddress_mgmt}/api/node/class/infraAccPortP.json', headers=headers, verify=False)
                intf_profiles = json.loads(r.text)
                if int(intf_profiles['totalCount']) > 0:
                    for intf in intf_profiles['imdata']:
                        intf_ipfs.append(intf['infraAccPortP']['attributes']['dn'].lstrip('uni/infra/accportprof-'))
                    # Save the Interface Profiles
                    targetDevice.interface_profiles = json.dumps(intf_ipfs)
                    targetDevice.save()
                    yield 'Interface Profile Config Options saved.<br>'
            except Exception as e:
                yield f'LoadAPICConfigListOptions (Exception) fetching configs on {targetDevice.device.name}. ({e})<br>'
                logger.error('LoadAPICConfigListOptions (Exception) fetching configs on {0}. {1}'.format(targetDevice.device.name, e))
                yield "<a href='%s'>Back to MOP Page</a><br>\n" % backLink
                continue
            # Get the Interface Policy Groups
            try:
                yield 'Gathering interface group policies from %s.<br>' % (targetDevice.device.name)
                intf_igps = []
                aci_token = apicCookie(targetDevice.device.ipaddress_mgmt, username, password)
                headers = {'Content-Type': 'application/json', 'Cookie': f'APIC-Cookie='+aci_token}
                r = requests.get(f'https://{targetDevice.device.ipaddress_mgmt}/api/node/class/infraAccPortGrp.json', headers=headers, verify=False)
                intf_groups = json.loads(r.text)
                if int(intf_groups['totalCount']) > 0:
                    for intf in intf_groups['imdata']:
                        intf_igps.append(intf['infraAccPortGrp']['attributes']['dn'].lstrip('uni/infra/funcprof/accportgrp-'))
                    # Save the Interface Group Policies
                    targetDevice.interface_policy_groups = json.dumps(intf_igps)
                    targetDevice.save()
                    yield 'Interface Policy Group Config Options saved.<br>'
            except Exception as e:
                yield f'LoadAPICConfigListOptions (Exception) fetching configs on {targetDevice.device.name}. ({e})<br>'
                logger.error('LoadAPICConfigListOptions (Exception) fetching configs on {0}. {1}'.format(targetDevice.device.name, e))
                yield "<a href='%s'>Back to MOP Page</a><br>\n" % backLink
                continue
    except Exception as e:
        yield f'LoadAPICConfigListOptions (Exception) fetching configs on {targetDevice.device.name} (outer). ({e})<br>'
        logger.error('LoadAPICConfigListOptions (Exception) fetching configs on {0} (outer). {1}'.format(targetDevice.device.name, e))
        yield "<a href='%s'>Back to MOP Page</a><br>\n" % backLink
        raise
    yield "</div></body></html>\n"