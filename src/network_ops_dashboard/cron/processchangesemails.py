import logging
from network_ops_dashboard.reports.changes.scripts.processchangesemail import *

logger = logging.getLogger('network_ops_dashboard')

# Process Changes Emails (In seperate cron folder to trigger at different time.)
logger.info(f"Cronjob: Process Changes Emails")
ProcessChangesEmails()