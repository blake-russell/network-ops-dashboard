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

def RunF5LBMopVipCertRenew(mop, reqUser, theme, creds):
    try:
        backLink = SiteSecrets.objects.filter(varname='backLink_f5lb_vipcertrenew')[0].varvalue
    except:
        backLink = '#'
    # Build StreamingHTTPresponse page
    yield "<html><head><title>F5 LB VIP Certificate Renew MOP</title>\n"
    yield "<link rel='stylesheet' href='/static/css/base.css'>\n"
    yield "<link rel='stylesheet' href='/static/css/style.css'>\n"
    if theme == 'themelight':
        yield "<link rel='stylesheet' href='https://bootswatch.com/5/lumen/bootstrap.css'></head>\n"
    else:
        yield "<link rel='stylesheet' href='https://bootswatch.com/5/cyborg/bootstrap.css'></head>\n"
    yield "<script src='https://code.jquery.com/jquery-3.6.0.min.js'></script>\n"
    yield "<script src='https://bootswatch.com/_vendor/bootstrap/dist/js/bootstrap.bundle.min.js'></script>\n"
    yield "Attempting to execute F5 LB VIP Cert Renew MOP {0}.\n".format(mop[0].name)
    yield "<hr>"
    yield '<div id="out" style="overflow:auto;">'
    # Testing javascript scrolling
    yield '<script>var out = document.getElementById("out");out.scrollTop = out.scrollHeight - out.clientHeight;</script>'
    # Log Event
    logger.info('F5LB VIPCertRenew MOP execution {0} initialized by {1}'.format(str(time.strftime("%m/%d/%y:%H:%M:%S:")),mop[0].name, reqUser))
    # Start of Script Logic
    yield "Validating load balancer active states.<br>\n"
    try:
        device = BIGIP(mop[0].device.name, creds[0].username, creds[0].password, session_verify=False)
        if f5lbCheckActiveState(mop[0].device.name, device) == True:
            yield "Target load balancer is active state and can proceed.<br>\n"
            targetDevice = mop[0].device.name
        else:
            # Change hostname
            if  str(mop[0].device.name)[-1] == '1':
                yield "Target load balancer is not active state, changing target to -02.<br>\n"
                targetDevice = str(mop[0].device.name)[:-1] + '2'
                device = BIGIP(targetDevice, creds[0].username, creds[0].password, session_verify=False)
            else:
                yield "Target load balancer is not active state, changing target to -01.<br>\n"
                targetDevice = str(mop[0].device.name)[:-1] + '1'
                device = BIGIP(targetDevice, creds[0].username, creds[0].password, session_verify=False)
    except Exception as e:
        yield "Exception connecting to load balancer(s): %s (MOP: %s)<br>\n" % (e, mop[0].name)
        logger.error('Exception connecting to load balancer(s): {0} (MOP: {1})'.format(e, mop[0].name))
        F5LBMopVipCertRenew.objects.filter(pk=mop[0].pk).update(status='Planned')
        yield "<a href='%s'>Back to MOP Page</a><br>\n" % backLink
        sys.exit(1)

    # Now we have a new 'device' with a session to the active load balancer if the original target was in standby
    # And we have a new variable 'targetDevice'

    # Validate virtual server & SSL Profile from MOP exists on the load balancer
    # Also grab the currently configured cert and key entries from the SSL profile to reference later in deletion process
    yield "Validating virtual server & SSL profile exists.<br>\n"
    yield " " * 1024  # Encourage browser to render incrementally
    try:
        if f5lbValidateServerExists(mop[0].virtual_server, device) == True:
            yield "Virtual server exists!<br>\n"
            profileCheck = f5lbSSLProfileExists(mop[0].ssl_policy, device)
            if profileCheck[0] == True:
                yield "Client SSL profile exists!<br>\n"
                # Returns old cert/key name as well
                # profileCheck[1].split('/Common/')[1] = Old Cert Name
                # profileCheck[3].split('/Common/')[1] = Old Cert Key Name
            else:
                yield "No client SSL profile with that name exists...Verify you have the correct client SSL profile name entered in the MOP.<br>\n"
                logger.error('No client SSL profile with that name exists: ({0} - MOP: {1})'.format(e, mop[0].name))
                F5LBMopVipCertRenew.objects.filter(pk=mop[0].pk).update(status='Planned')
                yield "<a href='%s'>Back to MOP Page</a><br>\n" % backLink
                sys.exit(1)
        else:
            yield "No virtual server with that name exists...Verify you have the correct virtual server name entered in the MOP.<br>\n"
            logger.error('No virtual server with that name exists: ({0} - MOP: {1})'.format(e, mop[0].name))
            F5LBMopVipCertRenew.objects.filter(pk=mop[0].pk).update(status='Planned')
            yield "<a href='%s'>Back to MOP Page</a><br>\n" % backLink
            sys.exit(1)
    except Exception as e:
        yield "Exception finding virtual server: %s (MOP: %s)<br>\n" % (e, mop[0].name)
        logger.error('Exception finding virtual server: {0} (MOP: {1})'.format(e, mop[0].name))
        F5LBMopVipCertRenew.objects.filter(pk=mop[0].pk).update(status='Planned')
        yield "<a href='%s'>Back to MOP Page</a><br>\n" % backLink
        sys.exit(1)

    # Upload and build new cert and key files/entries on the F5
    yield "Upload and build new cert and key files/entries on the F5 LB.<br>\n"
    yield " " * 1024  # Encourage browser to render incrementally
    try:
        device.upload(f'/mgmt/shared/file-transfer/uploads/', mop[0].cert_file.path)
        yield 'Certificate: %s, uploaded.<br>\n' % mop[0].cert_name
    except Exception as e:
        yield "Failed to upload certificate file. %s (MOP: %s)<br>\n" % (e, mop[0].name)
        logger.error('Failed to upload certificate file. {0} (MOP: {1})'.format(e, mop[0].name))
        F5LBMopVipCertRenew.objects.filter(pk=mop[0].pk).update(status='Planned')
        yield "<a href='%s'>Back to MOP Page</a><br>\n" % backLink
        sys.exit(1)
    try:
        device.upload(f'/mgmt/shared/file-transfer/uploads/', mop[0].cert_key_file.path)
        yield 'Key: %s, uploaded.<br>\n' % mop[0].cert_key_name
    except Exception as e:
        yield "Failed to upload key file. %s (MOP: %s)<br>\n" % (e, mop[0].name)
        logger.error('Failed to upload key file. {0} (MOP: {1})'.format(e, mop[0].name))
        F5LBMopVipCertRenew.objects.filter(pk=mop[0].pk).update(status='Planned')
        yield "<a href='%s'>Back to MOP Page</a><br>\n" % backLink
        sys.exit(1)
    # Create key entry in traffic certificate manager
    try:
        device.create('/mgmt/tm/sys/crypto/key/', {
            'command': 'install',
            'name': mop[0].cert_key_name,
            'from-local-file': f'/var/config/rest/downloads/{os.path.basename(mop[0].cert_key_file.path)}'
            })
        yield 'Key Entry: %s, created.<br>\n' % mop[0].cert_key_name
    except Exception as e:
        yield "Failed to create key entry in cert manager. %s (MOP: %s)<br>\n" % (e, mop[0].name)
        logger.error('Failed to create key entry in cert manager. {0} (MOP: {1})'.format(e, mop[0].name))
        F5LBMopVipCertRenew.objects.filter(pk=mop[0].pk).update(status='Planned')
        yield "<a href='%s'>Back to MOP Page</a><br>\n" % backLink
        sys.exit(1)
    # Create cerfificate entry in traffic certificate manager
    try:
        device.create('/mgmt/tm/sys/crypto/cert/', {
            'command': 'install',
            'name': mop[0].cert_name,
            'from-local-file': f'/var/config/rest/downloads/{os.path.basename(mop[0].cert_file.path)}'
            })
        yield 'Certificate entry: %s, created.<br>\n' % mop[0].cert_name
    except Exception as e:
        yield "Failed to create cert entry in cert manager. %s (MOP: %s)<br>\n" % (e, mop[0].name)
        logger.error('Failed to create cert entry in cert manager. {0} (MOP: {1})'.format(e, mop[0].name))
        F5LBMopVipCertRenew.objects.filter(pk=mop[0].pk).update(status='Planned')
        yield "<a href='%s'>Back to MOP Page</a><br>\n" % backLink
        sys.exit(1)
    # Delete cert and key file from the upload directories on the F5
    try:
        data = {}
        data['command'] = 'run'
        data['utilCmdArgs'] = f"-c 'rm -I /var/config/rest/downloads/{os.path.basename(mop[0].cert_file.path)}'"
        device.command('/mgmt/tm/util/bash', data)
        data['utilCmdArgs'] = f"-c 'rm -I /var/config/rest/downloads/{os.path.basename(mop[0].cert_key_file.path)}'"
        device.command('/mgmt/tm/util/bash', data)
        yield 'Certificate & Key files in upload directory deleted off of the F5.<br>\n'
    except Exception as e:
        yield "Failed to delete the certificate and key files from the upload directory off of the F5. %s (MOP: %s)<br>\n" % (e, mop[0].name)
        logger.error('Failed to delete the certificate and key files from the upload directory off of the F5. {0} (MOP: {1})'.format(e, mop[0].name))
        F5LBMopVipCertRenew.objects.filter(pk=mop[0].pk).update(status='Planned')
        yield "<a href='%s'>Back to MOP Page</a><br>\n" % backLink
        sys.exit(1)

    # Modify the SSL profile to add new cert/key/passphrase entry.
    yield "Modify the SSL profile with the new cert/key/passphrase entries.<br>\n"
    yield " " * 1024  # Encourage browser to render incrementally
    try:
        if mop[0].cert_key_pass != '':
            device.modify(f'/mgmt/tm/ltm/profile/client-ssl/{mop[0].ssl_policy}', {
                'cert': mop[0].cert_name,
                'key': mop[0].cert_key_name,
                'passphrase': mop[0].cert_key_pass
                })
            yield 'Successfully updated the cert/key/passphrase entries in the SSL profile.<br>\n'
        else:
            device.modify(f'/mgmt/tm/ltm/profile/client-ssl/{mop[0].ssl_policy}', {
                'cert': mop[0].cert_name,
                'key': mop[0].cert_key_name
                })
            yield 'Successfully updated the cert/key entries in the SSL profile.<br>\n'
    except Exception as e:
        yield "Failed to modify SSL profile with new cert/key entry. %s (MOP: %s)<br>\n" % (e, mop[0].name)
        logger.error('Failed to modify SSL profile with new cert/key entry. {0} (MOP: {1})'.format(e, mop[0].name))
        F5LBMopVipCertRenew.objects.filter(pk=mop[0].pk).update(status='Planned')
        yield "<a href='%s'>Back to MOP Page</a><br>\n" % backLink
        sys.exit(1)

    # Validation
    yield "Validating the new configuration.<br>\n"
    yield " " * 1024  # Encourage browser to render incrementally
    try:
        sslprofile = device.load(f'/mgmt/tm/ltm/profile/client-ssl/{mop[0].ssl_policy}')
        if sslprofile.properties['cert'].split('/Common/')[1] == mop[0].cert_name:
            yield 'SSL Profile: %s<br>\n' % mop[0].ssl_policy
            yield 'New Certificate Entry: %s<br>\n' % sslprofile.properties['cert'].split('/Common/')[1]
            yield 'New Key Entry: %s<br>\n' % sslprofile.properties['key'].split('/Common/')[1]
            try:
                if sslprofile.properties['passphrase'] != '':
                    yield 'New Key Passphrase: [Exists]<br>\n'
            except:
                yield 'Possibly misconfigured private key passphrase.<br>\n'
                pass
            F5LBMopVipCertRenew.objects.filter(pk=mop[0].pk).update(status='Completed')
            yield 'Please visit the load balancers web gui to validate and sync configuration: <a href="https://%s/xui">https://%s/xui</a><br>\n' % (targetDevice,targetDevice)
            yield "<a href='%s'>Back to MOP Page</a><br>\n" % backLink
            sys.exit(1)
        else:
            yield 'Post Validation of the SSL profile certificate (%s) does not match what is listed on the MOP: %s<br>\n' % (sslprofile.properties['cert'].split('/Common/')[1], mop[0].cert_name)
            logger.error('Post Validation of the SSL profile certificate  ({0})  does not match what is listed on the MOP: {1}. (MOP: {2})'.format(sslprofile.properties['cert'].split('/Common/')[1], mop[0].cert_name, mop[0].name))
            F5LBMopVipCertRenew.objects.filter(pk=mop[0].pk).update(status='Planned')
            yield "<a href='%s'>Back to MOP Page</a><br>\n" % backLink
    except Exception as e:
        yield "Exception validating the new configuration: %s (MOP: %s)<br>\n" % (e, mop[0].name)
        logger.error('Exception validating the new configuration: {0} (MOP: {1})'.format(e, mop[0].name))
        F5LBMopVipCertRenew.objects.filter(pk=mop[0].pk).update(status='Planned')
        yield "<a href='%s'>Back to MOP Page</a><br>\n" % backLink
        raise
    yield "</div></body></html>\n"