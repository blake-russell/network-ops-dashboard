# Register your models here.

from django.contrib import admin
from network_ops_dashboard.models import *
from network_ops_dashboard.f5lb.models import *
from network_ops_dashboard.asavpn.models import *
from network_ops_dashboard.reports.windstream.models import *
from network_ops_dashboard.inventory.models import *
from network_ops_dashboard.apic.models import *
from network_ops_dashboard.oncall.models import *

admin.site.register(WindstreamCktID)
admin.site.register(WindstreamMtcEmail)
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