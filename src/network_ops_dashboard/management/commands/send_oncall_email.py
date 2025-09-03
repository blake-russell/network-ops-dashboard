from django.core.management.base import BaseCommand
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils import timezone
from datetime import timedelta
from django.conf import settings
from django.db.models import Q
import logging
from premailer import transform
from django.core.mail import EmailMultiAlternatives
from network_ops_dashboard.models import FeatureFlags, SiteSettings
from network_ops_dashboard.reports.circuits.models import CircuitMtcEmail, CircuitProvider
from network_ops_dashboard.notices.certexpiry.models import CertExpiry
from network_ops_dashboard.notices.ciscoadvisory.models import CiscoAdvisory
from network_ops_dashboard.notices.svcactexpiry.models import SvcActExpiry
from network_ops_dashboard.oncall.models import OnCallIncident, OnCallSettings

logger = logging.getLogger(f'network_ops_dashboard.{__name__}')

def _incidents_for_report(settings_obj):
    days = max(settings_obj.report_window_days or 7, 1)
    since = timezone.now() - timedelta(days=days)
    qs = OnCallIncident.objects.filter(date_created__gte=since).exclude(status="Archived")
    if settings_obj.show_closed_in_report:
        return qs.order_by('-date_created')
    else:
        return qs.filter(status="Open").order_by('-date_created')
    
class Command(BaseCommand):
    help = "Render the on-call report and send it via email (HTML)."
    logger.info("On-call daily email cron started.")

    def handle(self, *args, **kwargs):
        flags = FeatureFlags.load()
        if not flags.enable_oncall_email:
            return
        
        settings_obj = OnCallSettings.load()

        base = (CircuitMtcEmail.objects
                .filter(status__in=['Planned','Completed','Cancelled','Updated','Demand','Emergency'])
                .order_by('startdatetime')
                .prefetch_related('circuits__provider', 'circuits__tag'))

        selected_tags = list(settings_obj.circuit_tags.values_list('pk', flat=True))
        if selected_tags:
            base = base.filter(circuits__tag__in=selected_tags).distinct()

        providers_with_emails = []
        if settings_obj.show_scheduled_maintenance:
            for provider in CircuitProvider.objects.all():
                emails_qs = base.filter(circuits__provider=provider).distinct()
                if emails_qs.exists():
                    providers_with_emails.append((provider, emails_qs))

        # incidents = OnCallIncident.objects.filter(status="Open").order_by('-date_created')
        incidents = incidents = _incidents_for_report(settings_obj)
        certs = CertExpiry.objects.filter(status='Open').order_by('expire_date') if settings_obj.show_cert_expiry else CertExpiry.objects.none()
        advisories = CiscoAdvisory.objects.filter(~Q(status='Archived')).order_by('date') if settings_obj.show_field_advisories else CiscoAdvisory.objects.none() 
        svc_acts = SvcActExpiry.objects.filter(status='Open').order_by('expire_date') if settings_obj.show_svcacct_expiry else SvcActExpiry.objects.none()

        site_settings = SiteSettings.objects.first()

        ctx = {
            "incidents": incidents,
            "providers_with_emails": providers_with_emails,
            "certs": certs,
            "advisories": advisories,
            "svc_acts": svc_acts,
            "site_settings": site_settings,
        }

        html = render_to_string("network_ops_dashboard/oncall/incident_email.html", ctx)
        html_inlined = transform(html, remove_classes=True, keep_style_tags=False)

        recipients = []
        for token in (flags.oncall_email_to or "").replace(";", ",").split(","):
            addr = token.strip()
            if addr:
                recipients.append(addr)
        if not recipients:
            return

        subject_prefix = site_settings.teamname if site_settings else "Team"
        subject_date = timezone.localdate()
        subject = f'{subject_prefix} Update - {subject_date.strftime("%m-%d-%Y")}'

        msg = EmailMultiAlternatives(
            subject=subject,
            body="This email is best viewed in HTML.",
            from_email=getattr(settings, "DEFAULT_FROM_EMAIL", None),
            to=recipients,
        )
        msg.attach_alternative(html_inlined, "text/html")
        msg.send()
        logger.info("On-call daily email sent.")