import requests
import logging
import time
import json
from network_ops_dashboard.models import *
from network_ops_dashboard.inventory.models import *
from network_ops_dashboard.apic.models import *
from network_ops_dashboard.apic.scripts.apic import apicCookie

logger = logging.getLogger('network_ops_dashboard.apic')


# Inputs from apic_createinterface_run view

# Create Interface (standard) - requires already configured Interface Profile, Selector, & IPG
def APICMopCreateInterfaceRun(mop, reqUser, theme, creds):
    try:
        backLink = SiteSecrets.objects.filter(varname='backLink_apic_createinterface')[0].varvalue
    except ImportError:
        backLink = '#'
    # Build StreamingHTTPresponse page
    yield "<html><head><title>APIC Create Interface MOP</title>\n"
    yield "<link rel='stylesheet' href='/static/css/base.css'>\n"
    yield "<link rel='stylesheet' href='/static/css/style.css'>\n"
    if theme == 'themelight':
        yield "<link rel='stylesheet' href='https://bootswatch.com/5/lumen/bootstrap.css'></head>\n"
    else:
        yield "<link rel='stylesheet' href='https://bootswatch.com/5/cyborg/bootstrap.css'></head>\n"
    yield "<script src='https://bootswatch.com/_vendor/jquery/dist/jquery.min.js'></script>\n"
    yield "<script src='https://bootswatch.com/_vendor/bootstrap/dist/js/bootstrap.bundle.min.js'></script>\n"
    yield "Attempting to execute APIC Create Interface MOP {0}.\n".format(mop[0].name)
    yield "<hr>"
    yield '<div id="out" style="overflow:auto;">'
    # Testing javascript scrolling
    yield '<script>var out = document.getElementById("out");out.scrollTop = out.scrollHeight - out.clientHeight;</script>'
    # Log Event
    logger.info('APIC Create Interface MOP execution {0} initialized by {1}'.format(str(time.strftime("%m/%d/%y:%H:%M:%S:")),mop[0].name, reqUser))
    # Start of Script Logic
    yield "Starting MOP Script<br>\n"
    yield " " * 1024  # Encourage browser to render incrementally
    try:
        for intf in mop[0].interfaces.all():
            aci_token = apicCookie(mop[0].device.ipaddress_mgmt, creds[0].username, creds[0].password)
            headers = {'Content-Type': 'application/json', 'Cookie': f'APIC-Cookie='+aci_token}
            try:
                payload = {
                    'infraHPortS': {
                        'attributes': {
                        'dn': f'uni/infra/accportprof-{intf.intfprofile}/hports-{intf.intfselector}-typ-range', 
                        'name': f'{intf.intfselector}',
                        'rn': f'hports-{intf.intfselector}-typ-range',
                        'status': 'created,modified'
                        },
                        'children': [
                            {
                                'infraPortBlk': {
                                    'attributes': {
                                        'dn': f'uni/infra/accportprof-{intf.intfprofile}/hports-{intf.intfselector}-typ-range/portblk-block2',
                                        'fromPort': f'{intf.intffromport}',
                                        'toPort': f'{intf.intftoport}',
                                        'name': 'block2',
                                        'descr': f'{intf.intfdesc}',
                                        'rn': 'portblk-block2',
                                        'status': 'created,modified'
                                    },
                                    "children": []
                                }
                            },
                            {
                                'infraRsAccBaseGrp': {
                                    'attributes': {
                                        'tDn': f'uni/infra/funcprof/accportgrp-{intf.intfipg}',
                                        'status': 'created,modified'
                                    },
                                    'children': []
                                }
                            }
                        ]
                    }
                }
                requests.post(f'https://{mop[0].device.ipaddress_mgmt}/api/node/mo/uni/infra/accportprof-{intf.intfprofile}/hports-{intf.intfselector}-typ-range.json', headers=headers, data=json.dumps(payload), verify=False)
                yield f'{intf.intfdesc} Successfully Created.<br>'
            except Exception as e:
                yield f'Exception creating {intf.intfdesc}. ({e})<br>'
                logger.error('Exception creating {0} APIC interface: {1} (MOP: {2})'.format(intf.intfdesc, e, mop[0].name))
                APICMopCreateInterface.objects.filter(pk=mop[0].pk).update(status='Planned')
                yield "<a href='%s'>Back to MOP Page</a><br>\n" % backLink
                raise
        yield "Successfully Completed APIC interface MOP: %s <br>\n" % (mop[0].name)
        logger.info('Successfully Completed APIC interface MOP: {0})'.format(mop[0].name))
        APICMopCreateInterface.objects.filter(pk=mop[0].pk).update(status='Completed')
        yield "<a href='%s'>Back to MOP Page</a><br>\n" % backLink
    except Exception as e:
        yield "Exception running APIC Create Interface MOP: %s (MOP: %s)<br>\n" % (e, mop[0].name)
        logger.error('Exception APIC interface MOP: {0} (MOP: {1})'.format(e, mop[0].name))
        APICMopCreateInterface.objects.filter(pk=mop[0].pk).update(status='Planned')
        yield "<a href='%s'>Back to MOP Page</a><br>\n" % backLink
        raise
    yield "</div></body></html>\n"
        