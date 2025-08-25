from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
import logging
from django.template.loader import render_to_string
from network_ops_dashboard.notices.pagerduty.models import PagerDutySettings, PagerDutyIncident
from network_ops_dashboard.models import FeatureFlags

logger = logging.getLogger('network_ops_dashboard.notices.pagerduty')

# Create your views here.

@login_required(login_url='/accounts/login/')
def pagerduty_card_partial_htmx(request):
    flags = FeatureFlags.load()
    cfg = PagerDutySettings.load()
    rows = []
    if flags.enable_pd_alarms:
        qs = PagerDutyIncident.objects.filter(active=True).order_by("-last_status_at")
        rows = list(qs.values(
            "incident_id","title","status","urgency","service_name","html_url","created_at","assignments"
        )[:cfg.top_n])
    html = render_to_string("network_ops_dashboard/notices/pagerduty/cards.html", {"rows": rows}, request=request)
    return HttpResponse(html)