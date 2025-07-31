import logging
from network_ops_dashboard.reports.circuits.models import *

logger = logging.getLogger('network_ops_dashboard.circuits')

def UpdateCircuitMtcStatus(email_list):
    logger.info(f"UpdateCircuitMtcStatus Running.")
    try:
        for mtc in email_list:
            logger.info(f"CircuitMtcEmail: MtcID: {mtc} auto-archived due to {mtc.status} status.")
            mtc.status = 'Auto-Archived'
            mtc.save()
    except Exception as e:
        logger.exception(f"Error auto-archiving CircuitMtcEmail: {e}")