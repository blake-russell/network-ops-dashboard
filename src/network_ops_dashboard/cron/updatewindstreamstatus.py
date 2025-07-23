import logging
from network_ops_dashboard.reports.windstream.models import *
from network_ops_dashboard.reports.windstream.scripts.updatewindstreamstatus import *

logger = logging.getLogger('network_ops_dashboard.windstream')
email_list_completed = WindstreamMtcEmail.objects.filter(status='Completed')
email_list_cancelled = WindstreamMtcEmail.objects.filter(status='Cancelled')

UpdateWindstreamStatus(email_list_completed)
UpdateWindstreamStatus(email_list_cancelled)