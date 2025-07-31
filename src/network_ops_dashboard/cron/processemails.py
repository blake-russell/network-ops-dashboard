import logging
from network_ops_dashboard.reports.circuits.models import *
from network_ops_dashboard.reports.circuits.scripts.processmtcemails import *
from network_ops_dashboard.reports.circuits.scripts.updatemtcstatus import *
from network_ops_dashboard.notices.certexpiry.scripts.processcertexpiryemail import *
from network_ops_dashboard.notices.ciscoadvisory.scripts.processciscoadvisoryemail import *
from network_ops_dashboard.notices.svcactexpiry.scripts.processsvcactexpiryemail import *

logger = logging.getLogger('network_ops_dashboard')

# Process Circuit Emails
logger.info(f"Cronjob: Process Circuit Emails")
circuit_id_list = Circuit.objects.all()
ProcessCircuitMtcEmails(circuit_id_list)
# Then process the emails
email_list_completed = CircuitMtcEmail.objects.filter(status='Completed')
email_list_cancelled = CircuitMtcEmail.objects.filter(status='Cancelled')
UpdateCircuitMtcStatus(email_list_completed)
UpdateCircuitMtcStatus(email_list_cancelled)

# Process CertExpiry Emails
logger.info(f"Cronjob: Process CertExpiry Emails")
ProcessCertExpiryEmails()

# Process CiscoAdvisory Emails
logger.info(f"Cronjob: Process CiscoAdvisory Emails")
ProcessCiscoAdvisoryEmails()

# Process SvcActExpiry Emails
logger.info(f"Cronjob: Process SvcActExpiry Emails")
ProcessSvcActExpiryEmails()