import os
import sys
import logging
import time
from network_ops_dashboard.models import *
from network_ops_dashboard.inventory.models import *
from network_ops_dashboard.f5lb.models import *
from network_ops_dashboard.f5lb.scripts.f5lb import *
from bigrest.bigip import BIGIP
#BIP-IP Version 16.1.4.1 - Build 0.50.5

logger = logging.getLogger('network_ops_dashboard.f5lb')


# Inputs from f5lb_vipcertrenew_run view

def RunF5LBMopVipCertRenew(playbook, reqUser, theme):
    # Build StreamingHTTPresponse page
    yield "<html><head><title>F5 LB VIP Certificate Renew Playbook</title>\n"
    yield "<link rel='stylesheet' href='/static/css/base.css'>\n"
    yield "<link rel='stylesheet' href='/static/css/style.css'>\n"
    if theme == 'themelight':
        yield "<link rel='stylesheet' href='https://bootswatch.com/5/lumen/bootstrap.css'></head>\n"
    else:
        yield "<link rel='stylesheet' href='https://bootswatch.com/5/cyborg/bootstrap.css'></head>\n"
    yield "<script src='https://code.jquery.com/jquery-3.6.0.min.js'></script>\n"
    yield "<script src='https://bootswatch.com/_vendor/bootstrap/dist/js/bootstrap.bundle.min.js'></script>\n"
    yield "Attempting to execute F5 LB VIP Cert Renew Playbook {0}.\n".format(playbook[0].name)
    yield "<hr>"
    yield '<div id="out" style="overflow:auto;">'
    # Testing javascript scrolling
    yield '<script>var out = document.getElementById("out");out.scrollTop = out.scrollHeight - out.clientHeight;</script>'
    # Log Event
    logger.info('F5LB VIPCertRenew Playbook execution {0} initialized by {1}'.format(str(time.strftime("%m/%d/%y:%H:%M:%S:")),playbook[0].name, reqUser))
    # Start of Script Logic
    yield "Validating load balancer active states.<br>\n"
    try:
        device = BIGIP(playbook[0].device.name, playbook[0].device.creds_rest.username, playbook[0].device.creds_rest.password, session_verify=False)
        if f5lbCheckActiveState(playbook[0].device.name, device) == True:
            yield "Target load balancer is active state and can proceed.<br>\n"
            targetDevice = playbook[0].device.name
        else:
            # Change hostname
            if  str(playbook[0].device.name)[-1] == '1':
                yield "Target load balancer is not active state, changing target to -02.<br>\n"
                targetDevice = str(playbook[0].device.name)[:-1] + '2'
                device = BIGIP(targetDevice, playbook[0].device.creds_rest.username, playbook[0].device.creds_rest.password, session_verify=False)
            else:
                yield "Target load balancer is not active state, changing target to -01.<br>\n"
                targetDevice = str(playbook[0].device.name)[:-1] + '1'
                device = BIGIP(targetDevice, playbook[0].device.creds_rest.username, playbook[0].device.creds_rest.password, session_verify=False)
    except Exception as e:
        yield "Exception connecting to load balancer(s): %s (Playbook: %s)<br>\n" % (e, playbook[0].name)
        logger.error('Exception connecting to load balancer(s): {0} (Playbook: {1})'.format(e, playbook[0].name))
        F5LBMopVipCertRenew.objects.filter(pk=playbook[0].pk).update(status='Planned')
        yield "<a href='../../'>Back to Playbook Page</a><br>\n"
        sys.exit(1)

    # Now we have a new 'device' with a session to the active load balancer if the original target was in standby
    # And we have a new variable 'targetDevice'

    # Validate virtual server & SSL Profile from Playbook exists on the load balancer
    # Also grab the currently configured cert and key entries from the SSL profile to reference later in deletion process
    yield "Validating virtual server & SSL profile exists.<br>\n"
    yield " " * 1024  # Encourage browser to render incrementally
    try:
        if f5lbValidateServerExists(playbook[0].virtual_server, device) == True:
            yield "Virtual server exists!<br>\n"
            profileCheck = f5lbSSLProfileExists(playbook[0].ssl_policy, device)
            if profileCheck[0] == True:
                yield "Client SSL profile exists!<br>\n"
                # Returns old cert/key name as well
                # profileCheck[1].split('/Common/')[1] = Old Cert Name
                # profileCheck[3].split('/Common/')[1] = Old Cert Key Name
            else:
                yield "No client SSL profile with that name exists...Verify you have the correct client SSL profile name entered in the Playbook.<br>\n"
                logger.error('No client SSL profile with that name exists: ({0} - Playbook: {1})'.format(e, playbook[0].name))
                F5LBMopVipCertRenew.objects.filter(pk=playbook[0].pk).update(status='Planned')
                yield "<a href='../../'>Back to playbook Page</a><br>\n"
                sys.exit(1)
        else:
            yield "No virtual server with that name exists...Verify you have the correct virtual server name entered in the Playbook.<br>\n"
            logger.error('No virtual server with that name exists: ({0} - Playbook: {1})'.format(e, playbook[0].name))
            F5LBMopVipCertRenew.objects.filter(pk=playbook[0].pk).update(status='Planned')
            yield "<a href='../../'>Back to Playbook Page</a><br>\n"
            sys.exit(1)
    except Exception as e:
        yield "Exception finding virtual server: %s (Playbook: %s)<br>\n" % (e, playbook[0].name)
        logger.error('Exception finding virtual server: {0} (Playbook: {1})'.format(e, playbook[0].name))
        F5LBMopVipCertRenew.objects.filter(pk=playbook[0].pk).update(status='Planned')
        yield "<a href='../../'>Back to Playbook Page</a><br>\n"
        sys.exit(1)

    # Upload and build new cert and key files/entries on the F5
    yield "Upload and build new cert and key files/entries on the F5 LB.<br>\n"
    yield " " * 1024  # Encourage browser to render incrementally
    try:
        device.upload(f'/mgmt/shared/file-transfer/uploads/', playbook[0].cert_file.path)
        yield 'Certificate: %s, uploaded.<br>\n' % playbook[0].cert_name
    except Exception as e:
        yield "Failed to upload certificate file. %s (Playbook: %s)<br>\n" % (e, playbook[0].name)
        logger.error('Failed to upload certificate file. {0} (Playbook: {1})'.format(e, playbook[0].name))
        F5LBMopVipCertRenew.objects.filter(pk=playbook[0].pk).update(status='Planned')
        yield "<a href='../../'>Back to Playbook Page</a><br>\n"
        sys.exit(1)
    try:
        device.upload(f'/mgmt/shared/file-transfer/uploads/', playbook[0].cert_key_file.path)
        yield 'Key: %s, uploaded.<br>\n' % playbook[0].cert_key_name
    except Exception as e:
        yield "Failed to upload key file. %s (Playbook: %s)<br>\n" % (e, playbook[0].name)
        logger.error('Failed to upload key file. {0} (Playbook: {1})'.format(e, playbook[0].name))
        F5LBMopVipCertRenew.objects.filter(pk=playbook[0].pk).update(status='Planned')
        yield "<a href='../../'>Back to Playbook Page</a><br>\n"
        sys.exit(1)
    # Create key entry in traffic certificate manager
    try:
        device.create('/mgmt/tm/sys/crypto/key/', {
            'command': 'install',
            'name': playbook[0].cert_key_name,
            'from-local-file': f'/var/config/rest/downloads/{os.path.basename(playbook[0].cert_key_file.path)}'
            })
        yield 'Key Entry: %s, created.<br>\n' % playbook[0].cert_key_name
    except Exception as e:
        yield "Failed to create key entry in cert manager. %s (Playbook: %s)<br>\n" % (e, playbook[0].name)
        logger.error('Failed to create key entry in cert manager. {0} (Playbook: {1})'.format(e, playbook[0].name))
        F5LBMopVipCertRenew.objects.filter(pk=playbook[0].pk).update(status='Planned')
        yield "<a href='../../'>Back to Playbook Page</a><br>\n"
        sys.exit(1)
    # Create cerfificate entry in traffic certificate manager
    try:
        device.create('/mgmt/tm/sys/crypto/cert/', {
            'command': 'install',
            'name': playbook[0].cert_name,
            'from-local-file': f'/var/config/rest/downloads/{os.path.basename(playbook[0].cert_file.path)}'
            })
        yield 'Certificate entry: %s, created.<br>\n' % playbook[0].cert_name
    except Exception as e:
        yield "Failed to create cert entry in cert manager. %s (Playbook: %s)<br>\n" % (e, playbook[0].name)
        logger.error('Failed to create cert entry in cert manager. {0} (Playbook: {1})'.format(e, playbook[0].name))
        F5LBMopVipCertRenew.objects.filter(pk=playbook[0].pk).update(status='Planned')
        yield "<a href='../../'>Back to Playbook Page</a><br>\n"
        sys.exit(1)
    # Delete cert and key file from the upload directories on the F5
    try:
        data = {}
        data['command'] = 'run'
        data['utilCmdArgs'] = f"-c 'rm -I /var/config/rest/downloads/{os.path.basename(playbook[0].cert_file.path)}'"
        device.command('/mgmt/tm/util/bash', data)
        data['utilCmdArgs'] = f"-c 'rm -I /var/config/rest/downloads/{os.path.basename(playbook[0].cert_key_file.path)}'"
        device.command('/mgmt/tm/util/bash', data)
        yield 'Certificate & Key files in upload directory deleted off of the F5.<br>\n'
    except Exception as e:
        yield "Failed to delete the certificate and key files from the upload directory off of the F5. %s (Playbook: %s)<br>\n" % (e, playbook[0].name)
        logger.error('Failed to delete the certificate and key files from the upload directory off of the F5. {0} (Playbook: {1})'.format(e, playbook[0].name))
        F5LBMopVipCertRenew.objects.filter(pk=playbook[0].pk).update(status='Planned')
        yield "<a href='../../'>Back to Playbook Page</a><br>\n"
        sys.exit(1)

    # Modify the SSL profile to add new cert/key/passphrase entry.
    yield "Modify the SSL profile with the new cert/key/passphrase entries.<br>\n"
    yield " " * 1024  # Encourage browser to render incrementally
    try:
        if playbook[0].cert_key_pass != '':
            device.modify(f'/mgmt/tm/ltm/profile/client-ssl/{playbook[0].ssl_policy}', {
                'cert': playbook[0].cert_name,
                'key': playbook[0].cert_key_name,
                'passphrase': playbook[0].cert_key_pass
                })
            yield 'Successfully updated the cert/key/passphrase entries in the SSL profile.<br>\n'
        else:
            device.modify(f'/mgmt/tm/ltm/profile/client-ssl/{playbook[0].ssl_policy}', {
                'cert': playbook[0].cert_name,
                'key': playbook[0].cert_key_name
                })
            yield 'Successfully updated the cert/key entries in the SSL profile.<br>\n'
    except Exception as e:
        yield "Failed to modify SSL profile with new cert/key entry. %s (Playbook: %s)<br>\n" % (e, playbook[0].name)
        logger.error('Failed to modify SSL profile with new cert/key entry. {0} (Playbook: {1})'.format(e, playbook[0].name))
        F5LBMopVipCertRenew.objects.filter(pk=playbook[0].pk).update(status='Planned')
        yield "<a href='../../'>Back to Playbook Page</a><br>\n"
        sys.exit(1)

    # Validation
    yield "Validating the new configuration.<br>\n"
    yield " " * 1024  # Encourage browser to render incrementally
    try:
        sslprofile = device.load(f'/mgmt/tm/ltm/profile/client-ssl/{playbook[0].ssl_policy}')
        if sslprofile.properties['cert'].split('/Common/')[1] == playbook[0].cert_name:
            yield 'SSL Profile: %s<br>\n' % playbook[0].ssl_policy
            yield 'New Certificate Entry: %s<br>\n' % sslprofile.properties['cert'].split('/Common/')[1]
            yield 'New Key Entry: %s<br>\n' % sslprofile.properties['key'].split('/Common/')[1]
            try:
                if sslprofile.properties['passphrase'] != '':
                    yield 'New Key Passphrase: [Exists]<br>\n'
            except:
                yield 'Possibly misconfigured private key passphrase.<br>\n'
                pass
            F5LBMopVipCertRenew.objects.filter(pk=playbook[0].pk).update(status='Completed')
            yield 'Please visit the load balancers web gui to validate and sync configuration: <a href="https://%s/xui">https://%s/xui</a><br>\n' % (targetDevice,targetDevice)
            yield "<a href='../../'>Back to Playbook Page</a><br>\n"
            sys.exit(1)
        else:
            yield 'Post Validation of the SSL profile certificate (%s) does not match what is listed on the Playbook: %s<br>\n' % (sslprofile.properties['cert'].split('/Common/')[1], mop[0].cert_name)
            logger.error('Post Validation of the SSL profile certificate  ({0})  does not match what is listed on the Playbook: {1}. (Playbook: {2})'.format(sslprofile.properties['cert'].split('/Common/')[1], mop[0].cert_name, mop[0].name))
            F5LBMopVipCertRenew.objects.filter(pk=playbook[0].pk).update(status='Planned')
            yield "<a href='../../'>Back to Playbook Page</a><br>\n"
    except Exception as e:
        yield "Exception validating the new configuration: %s (Playbook: %s)<br>\n" % (e, playbook[0].name)
        logger.error('Exception validating the new configuration: {0} (Playbook: {1})'.format(e, playbook[0].name))
        F5LBMopVipCertRenew.objects.filter(pk=playbook[0].pk).update(status='Planned')
        yield "<a href='../../'>Back to Playbook Page</a><br>\n"
        raise
    yield "</div></body></html>\n"