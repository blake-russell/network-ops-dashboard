from django.db.models import Avg
from network_ops_dashboard.sdwan.vmanage.models import SdwanPathStat
from django.utils import timezone
from datetime import datetime, timedelta
from django.db.models import Avg
import requests


def top_sites_by_latency(n, minutes):
    since = timezone.now() - timedelta(minutes=minutes)
    qs = (SdwanPathStat.objects
          .filter(collected_at__gte=since)
          .values("host_name")
          .annotate(avg_lat=Avg("latency_ms"), avg_jit=Avg("jitter_ms"), avg_loss=Avg("loss_pct"))
          .order_by("-avg_lat")[:n])

    rows = [{
            "site": r["host_name"],
            "avg_latency_ms": round(r["avg_lat"] or 0),
            "avg_jitter_ms": round(r["avg_jit"] or 0),
            "avg_loss_pct": round(r["avg_loss"] or 0.0, 1),
        } for r in qs]
    return rows

class VManage:
    def __init__(self, base, user, pwd, verify=True):
        self.base = base.rstrip("/")
        self.user = user
        self.pwd = pwd
        self.verify = verify
        self.session = requests.Session()
        self.xsrf = None

    def login(self):
        # JSESSIONID
        r = self.session.post(
            f"{self.base}/j_security_check",
            data={"j_username": self.user, "j_password": self.pwd},
            verify=self.verify,
            timeout=30,
        )
        if "JSESSIONID" not in self.session.cookies:
            raise RuntimeError("vManage auth failed (no JSESSIONID)")
        # XSRF token
        r = self.session.get(f"{self.base}/dataservice/client/token",
                             verify=self.verify, timeout=30)
        if r.ok and r.text:
            self.xsrf = r.text.strip()
            self.session.headers["X-XSRF-TOKEN"] = self.xsrf

    def get_approute(self, minutes):
        """
        Pull recent app-route stats. 
        /dataservice/statistics/approute
        """
        q = {
            "query": {
                "condition": "AND",
                "rules": [{
                    "field": "entry_time",
                    "type": "date",
                    "operator": "last_n_minutes",
                    "value": minutes
                }]
            },
            "aggregation": {
                "field": [{"property": "loss", "type":"avg"},
                          {"property": "latency", "type":"avg"},
                          {"property": "jitter", "type":"avg"}],
                "interval": 0
            }
        }
        r = self.session.get(f"{self.base}/dataservice/statistics/approute",
                              json=q, verify=self.verify, timeout=45)
        r.raise_for_status()
        return r.json().get("data", [])
    
    def _epoch_ms_to_dt(self, ms):
        try:
            return datetime.fromtimestamp(int(ms) / 1000.0, tz=timezone.utc)
        except Exception:
            return None

    def _mk_tunnel_id(self, d):
        return f"{d.get('local_system_ip')}:{d.get('local_color')}->" \
		    f"{d.get('remote_system_ip')}:{d.get('remote_color')}"

    def CollectVmanageStats(s, f, now):
        vm = VManage(s.host.name_lookup, s.host.creds_rest.username, s.host.creds_rest.password, s.verify_ssl)
        vm.login()
        rows = vm.get_approute(minutes=f.sdwan_interval_minutes)
    
        # Wipe ‘old’ object entries and keep latest run
        cutoff = now - timedelta(hours=s.purge_path_stats)
        SdwanPathStat.objects.filter(collected_at__lt=cutoff).delete()

        objs = []
        for d in rows:
            tunnel_id = vm._mk_tunnel_id(d)
            entry_dt = vm._epoch_ms_to_dt(d.get("entry_time"))
    
            objs.append(SdwanPathStat(
                tunnel_id=tunnel_id,
                local_system_ip=d.get("local_system_ip"),
                remote_system_ip=d.get("remote_system_ip"),
                local_color=d.get("local_color"),
                remote_color=d.get("remote_color"),
                device_model=d.get("device_model") or "",
                host_name=d.get("host_name") or "",
                proto=d.get("proto") or "",
                latency_ms=float(d.get("latency") or 0),
                jitter_ms=float(d.get("jitter") or 0),
                loss_pct=float(d.get("loss_percentage") if d.get("loss_percentage") is not None else d.get("loss") or 0),
                vqoe_score=float(d.get("vqoe_score") or 0),
                tx_pkts=int(d.get("tx_pkts") or 0),
                rx_pkts=int(d.get("rx_pkts") or 0),
                tx_octets=int(d.get("tx_octets") or 0),
                rx_octets=int(d.get("rx_octets") or 0),
                state=d.get("state") or "",
                entry_time=entry_dt,
                ))
    	
    	# Store fresh rows
        SdwanPathStat.objects.bulk_create(objs, ignore_conflicts=True)