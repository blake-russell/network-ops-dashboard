import logging
import json
from collections.abc import Iterable
from django.db.models.query import QuerySet
from network_ops_dashboard.models import *
from network_ops_dashboard.inventory.models import *
from network_ops_dashboard.f5lb.models import *
from bigrest.bigip import BIGIP
#BIP-IP Version 16.1.4.1 - Build 0.50.5

logger = logging.getLogger('network_ops_dashboard.f5lb')


def LoadF5LBConfigListsOptions(deviceList, reqUser, theme):
    # Build StreamingHTTPresponse page
    yield "<html><head><title>F5 LB Loading Config Options into DB</title>\n"
    yield "<link rel='stylesheet' href='/static/css/base.css'>\n"
    yield "<link rel='stylesheet' href='/static/css/style.css'>\n"
    if theme == 'themelight':
        yield "<link rel='stylesheet' href='https://bootswatch.com/5/lumen/bootstrap.css'></head>\n"
    else:
        yield "<link rel='stylesheet' href='https://bootswatch.com/5/cyborg/bootstrap.css'></head>\n"
    yield "<script src='https://code.jquery.com/jquery-3.6.0.min.js'></script>\n"
    yield "<script src='https://bootswatch.com/_vendor/bootstrap/dist/js/bootstrap.bundle.min.js'></script>\n"
    yield "<hr>"
    yield '<div id="out" style="overflow:auto;">'
    # Testing javascript scrolling
    yield '<script>var out = document.getElementById("out");out.scrollTop = out.scrollHeight - out.clientHeight;</script>'
    logger.info('F5LB LoadF5LBConfigListOptions initialized by %s' %(reqUser))
    try:
        yield " " * 1024  # Encourage browser to render incrementally
        if not isinstance(deviceList, (list, QuerySet)):
            deviceList = [deviceList]
        for targetDevice in deviceList:
            device = BIGIP(targetDevice.device.name, targetDevice.device.creds_rest.username, targetDevice.device.creds_rest.password, session_verify=False)
            virtuals = []
            profiles = []
            try:
                yield 'Gathering config options from %s.<br>' % (targetDevice.device.name)
                for virtual in device.show(f'/mgmt/tm/ltm/virtual'):
                    virtuals.append(virtual.properties['tmName']['description'].lstrip('/Common/'))
                for profile in device.show(f'/mgmt/tm/ltm/profile/client-ssl'):
                    profiles.append(profile.properties['tmName']['description'].lstrip('/Common/'))
                # set F5LBConfigOptions for device
                targetDevice.virtual_servers = json.dumps(virtuals)
                targetDevice.ssl_policies =  json.dumps(profiles)
                # save model
                targetDevice.save()
                yield 'Config Options saved.<br>'
            except KeyError as k:
                yield "Error loading config options from: %s. (Are there config options to pull?)<br>" % (targetDevice.device.name)
                logger.exception('LoadF5LBConfigListsOptions: Exception loading virtuals/profiles for %s: %s' % (targetDevice.device.name, k))
                continue
    except Exception as e:
        yield "LoadF5LBConfigListsOptions: Exception connecting to load balancer(s): %s<br>" % (targetDevice.device.name)
        yield "Exception: %s<br>" % (e)
        yield "<a href='../../'>Back to Playbook Page</a><br>\n"
        yield "</div></body></html>\n"
        logger.exception('LoadF5LBConfigListsOptions: Exception connecting to load balancer(s): %s' % (e))
        raise
    yield "<a href='../../'>Back to Playbook Page</a><br>\n"
    yield "</div></body></html>\n"