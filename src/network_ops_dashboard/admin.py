# Register your models here.

from django.contrib import admin
from network_ops_dashboard.models import *
from network_ops_dashboard.f5lb.models import *
from network_ops_dashboard.asavpn.models import *
from network_ops_dashboard.reports.circuits.models import *
from network_ops_dashboard.reports.changes.models import *
from network_ops_dashboard.notices.certexpiry.models import *
from network_ops_dashboard.notices.ciscoadvisory.models import *
from network_ops_dashboard.notices.svcactexpiry.models import *
from network_ops_dashboard.inventory.models import *
from network_ops_dashboard.apic.models import *
from network_ops_dashboard.oncall.models import *

admin.site.register(Site)
admin.site.register(Platform)
admin.site.register(Inventory)
admin.site.register(NetworkCredential)
admin.site.register(AsaVpnDiscoLog)
admin.site.register(DeviceTag)
admin.site.register(AsaVpnConnectedUsers)
admin.site.register(F5LBMopVipCertRenew)
admin.site.register(APICMopCreateInterface)
admin.site.register(APICMopInterface)
admin.site.register(F5LBConfigOptions)
admin.site.register(APICConfigOptions)
admin.site.register(OnCallIncident)
admin.site.register(SiteSettings)
admin.site.register(SiteSettingsWebsite)
admin.site.register(SiteSecrets)
admin.site.register(CompanyChanges)
admin.site.register(CertExpiry)
admin.site.register(CertProvider)
admin.site.register(CiscoAdvisory)
admin.site.register(SvcActExpiry)
admin.site.register(CircuitProvider)
admin.site.register(CircuitTag)
admin.site.register(Circuit)
admin.site.register(CircuitMtcEmail)