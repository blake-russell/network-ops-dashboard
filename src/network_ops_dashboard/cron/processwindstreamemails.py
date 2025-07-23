import logging
from network_ops_dashboard.reports.windstream.models import *
from network_ops_dashboard.reports.windstream.scripts.processwindstreamemails import *

logger = logging.getLogger('network_ops_dashboard.windstream')
#circuit_id_list = WindstreamCktID.objects.all()
circuit_id_list = {
    normalize_circuit_id(c.cktid): c
    for c in WindstreamCktID.objects.all()
}

ProcessWindstreamEmails(circuit_id_list)