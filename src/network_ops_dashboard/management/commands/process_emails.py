import logging
from django.core.management.base import BaseCommand
from django.utils import timezone

logger = logging.getLogger(f'network_ops_dashboard.{__name__}')

class Command(BaseCommand):
    help = "Process emails for Reports and Notices."

    def add_arguments(self, parser):
        parser.add_argument(
            "--force", action="store_true",
            help="Run regardless of last_run/time gate (for debugging)"
        )

    def handle(self, *args, **kwargs):
        from network_ops_dashboard.models import FeatureFlags
        from network_ops_dashboard.reports.circuits.models import Circuit, CircuitMtcEmail
        from network_ops_dashboard.reports.circuits.scripts.processmtcemails import ProcessCircuitMtcEmails
        from network_ops_dashboard.reports.circuits.scripts.updatemtcstatus import UpdateCircuitMtcStatus
        from network_ops_dashboard.notices.certexpiry.scripts.processcertexpiryemail import ProcessCertExpiryEmails
        from network_ops_dashboard.notices.svcactexpiry.scripts.processsvcactexpiryemail import ProcessSvcActExpiryEmails
        from network_ops_dashboard.notices.ciscoadvisory.scripts.processciscoadvisoryemail import ProcessCiscoAdvisoryEmails
        from network_ops_dashboard.reports.changes.scripts.processchangesemail import ProcessChangesEmails

        flags = FeatureFlags.load()
        if not flags.enable_email_processing:
            logger.info("Email processing disabled. Exiting.")
            return
        
        results = []

        def _run(label, fn, *fargs, **fkwargs):
            try:
                logger.info("running %s...", label)
                out = fn(*fargs, **fkwargs)
                results.append((label, "ok", out))
                logger.info("%s complete.", label)
            except Exception as e:
                logger.exception("%s failed: %s", label, e)
                results.append((label, "failed", str(e)))

        logger.info("Email processing started.")

        # Process Circuit Emails
        logger.info(f"Cronjob: Process Circuit Emails")
        circuit_id_list = Circuit.objects.all()
        ProcessCircuitMtcEmails(circuit_id_list)
        
        # Update CircuitMtc Status
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

        # Process Changes Emails
        logger.info(f"Cronjob: Process Changes Emails")
        ProcessChangesEmails()

        logger.info("Email processing completed.")