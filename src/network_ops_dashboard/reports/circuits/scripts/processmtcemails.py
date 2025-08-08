import logging
from importlib import import_module
from network_ops_dashboard.reports.circuits.models import *
from network_ops_dashboard.reports.circuits.scripts.processhandlers import *

logger = logging.getLogger('network_ops_dashboard.circuits')

def import_by_path(dotted_path):
    module_path, func_name = dotted_path.rsplit('.', 1)
    module = import_module(module_path)
    return getattr(module, func_name)

def normalize_circuit_id(s):
    # Remove all slashes and whitespace
    return re.sub(r'[\s/]+', '', s).upper()

def ProcessCircuitMtcEmails(circuit_id_list):
    logger.info("ProcessCircuitMtcEmails Running.")

    FULL_HANDLER_PATH = "network_ops_dashboard.reports.circuits.scripts.processhandlers"

    for provider in CircuitProvider.objects.all():
        provider_name = provider.name
        func_name = provider.function_name
        folder_path = provider.email_folder

        provider_circuit_id_list = {
            normalize_circuit_id(c.cktid): c
            for c in Circuit.objects.filter(provider__name=provider_name)
        }

        if not func_name or not folder_path:
            logger.warning(f"No function_name or email_folder configured for '{provider_name}', skipping.")
            continue

        try:
            # Send to Process Handler
            full_path = f"{FULL_HANDLER_PATH}.{func_name}"
            func = import_by_path(full_path)
            func(folder_path, provider_circuit_id_list)
        except Exception as e:
            # Throws exception if there is not a process handler in processhandlers.py.
            logger.exception(f"No process handler for '{provider_name}': {e}")
            continue
    return None