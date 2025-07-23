import logging
from network_ops_dashboard.reports.windstream.models import *

logger = logging.getLogger('network_ops_dashboard.windstream')

def UpdateWindstreamStatus(email_list):
    logger.info(f"UpdateWindstreamStatus Running.")
    try:
        for email in email_list:
            logger.info(f"WindstreamMtcEmail WMT: {email} auto-archived due to {email.status} status.")
            email.status = 'Auto-Archived'
            email.save()
    except Exception as e:
        logger.exception(f"Error auto-archiving WindstreamMtcEmail: {e}")