import threading
import logging
from network_ops_dashboard.inventory.discovery.scripts.services import run_discovery
from network_ops_dashboard.inventory.discovery.models import DiscoveryJob

logger = logging.getLogger(__name__)

def run_discovery_job(job_id):
    # Run the discovery and update job state
    try:
        job = DiscoveryJob.objects.get(pk=job_id)
        job.mark_running()
        count, created_count, error_count, ignored_count, summary= run_discovery(job)
        if error_count > 0:
            job.mark_error
        job.mark_done(count=count, summary=summary)
        logger.info("Discovery job %s completed: %s", job.id, summary)
    except Exception as e:
        logger.exception("Discovery job %s failed", job_id)
        try:
            job = DiscoveryJob.objects.get(pk=job_id)
            job.mark_error(str(e))
        except Exception:
            pass

def start_discovery_in_thread(job_id):
    # Spawn a background thread for discovery
    thread = threading.Thread(target=run_discovery_job, args=(job_id,))
    thread.daemon = True  # exit if process dies
    thread.start()