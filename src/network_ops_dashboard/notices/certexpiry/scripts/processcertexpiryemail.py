import logging
from importlib import import_module
from network_ops_dashboard.notices.certexpiry.models import *
from network_ops_dashboard.notices.certexpiry.scripts.processhandlers import *

logger = logging.getLogger('network_ops_dashboard.certexpiry')

def import_by_path(dotted_path):
    module_path, func_name = dotted_path.rsplit('.', 1)
    module = import_module(module_path)
    return getattr(module, func_name)

def ProcessCertExpiryEmails():
    logger.info(f"ProcessCertExpiryEmails Running.")

    FULL_HANDLER_PATH = "network_ops_dashboard.notices.certexpiry.scripts.processhandlers"

    for provider in CertProvider.objects.all():
        provider_name = provider.name
        func_name = provider.function_name
        folder_path = provider.certexpiry_folder

        if not func_name or not folder_path:
            logger.warning(f"No function_name or certexpiry_folder configured for '{provider_name}', skipping.")
            continue

        try:
            # Send to Process Handler
            full_path = f"{FULL_HANDLER_PATH}.{func_name}"
            func = import_by_path(full_path)
            func(provider, folder_path)
        except Exception as e:
            # Throws exception if there is not a process handler in processhandlers.py.
            logger.exception(f"No process handler for '{provider_name}': {e}")
            continue
        
    return None