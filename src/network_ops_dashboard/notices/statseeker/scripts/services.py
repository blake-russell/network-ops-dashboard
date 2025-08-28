import requests
from django.db import transaction
from django.utils import timezone
from decimal import Decimal, InvalidOperation
import logging
from network_ops_dashboard.notices.statseeker.models import StatseekerSettings, StatseekerAlert
from network_ops_dashboard.inventory.models import Inventory

logger = logging.getLogger('network_ops_dashboard.notices.statseeker')

def _tracked_interfaces(inv: Inventory):
    # Inventory.priority_interfaces is a comma-separated string.
    try:
        return inv.get_priority_interfaces()
    except Exception:
        # fallback if needed
        s = (inv.priority_interfaces or "").strip()
        return [p.strip() for p in s.split(",") if p.strip()]

def _SScookie(base, auth, verifySSL):
    headers = { 'Accept': 'application/json', 'Content-Type': 'application/x-www-form-urlencoded' }
    authData = {'user': auth[0], 'password': auth[1]}
    r = requests.post(f'{base}/ss-auth', headers=headers, data=authData, verify=verifySSL)
    return r.json()["access_token"]

def _index_by_id(device_list):
    # device_list = [{'id': 6318048, 'name': 'DALLAS-DC-RTR-02', 'ipaddress': '10.10.10.252'}, ...]
    # Map Statseeker id -> device dict.'''
    return {d.get('id') or d.get('deviceid'): d for d in device_list}

def _filter_list(values):
    vals = [str(v).strip() for v in (values if isinstance(values, (list, tuple, set)) else [values]) if v is not None and str(v).strip()]
    if not vals:
        return None
    return f'IS("{vals[0]}")' if len(vals) == 1 else 'IN(' + ','.join(f'"{v}"' for v in vals) + ')'

def _is_up(v):
    """Accepts 1/'1'/'up'/'Up'/True; returns bool"""
    if v is None:
        return False
    if isinstance(v, bool):
        return v
    if isinstance(v, int):
        return v == 1
    s = str(v).strip().lower()
    return s in ("1", "up", "true", "on")

def _is_admin_up(v): return _is_up(v)

def _as_decimal(val):
    try:
        return float(val)
    except Exception:
        return None
    
def _to_decimal(v):
    if v is None:
        return None
    try:
        return Decimal(str(v))
    except (InvalidOperation, ValueError, TypeError):
        return None

def _build_device_ip_list(base, auth, headers, verifySSL, tracked):
    devices = [x.ipaddress_mgmt for x in tracked if x.ipaddress_mgmt]
    ipaddress_list = _filter_list(devices)
    if not ipaddress_list:
        return {"data": {"objects": [{"data": []}]}}
    query = f'/api/latest/cdt_device?fields=id,name,ipaddress&ipaddress_filter={ipaddress_list}'
    r = requests.get(f"{base}{query}", headers=headers, auth=auth, verify=verifySSL, timeout=20)
    r.raise_for_status()
    return r.json()['data']['objects'][0]['data']

def _device_ping_state(base, auth, headers, verifySSL, device_list):
    devices = [x['id'] for x in device_list if x['id']]
    devices_list = _filter_list(devices)
    if not devices_list:
        return {"data": {"objects": [{"data": []}]}}
    query = f'/api/latest/cdt_device?fields=deviceid,name,ipaddress,ping_state&deviceid_filter={devices_list}'
    r = requests.get(f"{base}{query}", headers=headers, auth=auth, verify=verifySSL, timeout=20)
    r.raise_for_status()
    return r.json()

def _merge_ping_states(device_list, r_json):
    # Merge ping_state results from the cdt_device call into device_list.
    # ['data']['objects'][*]['data']
    idx = _index_by_id(device_list)
    objects = (r_json or {}).get('data', {}).get('objects', []) or []
    for obj in objects:
        for row in obj.get('data', []) or []:
            dev_id = row.get('deviceid') or row.get('id')
            if dev_id in idx:
                idx[dev_id]['ping_state'] = row.get('ping_state')  # 'up'/'down'/etc.

def _get_tracked_interfaces(base, auth, headers, verifySSL, device_id, if_names):
    # Example matches your sample: /cdt_port?fields=...&deviceid_filter=IS("6318048")&name_filter=IS("Eth1/43","Eth2/43")
    devices_list = _filter_list(device_id)
    name_list = _filter_list(if_names)
    if not (name_list and devices_list):
        return []
    query = f'/api/latest/cdt_port?fields=id,name,deviceid,ifAdminStatus,ifOperStatus,RxTxErrorPercent&RxTxErrorPercent_formats=total&deviceid_filter={devices_list}&name_filter={name_list}'
    r = requests.get(f"{base}{query}", headers=headers, auth=auth, verify=verifySSL, timeout=20)
    r.raise_for_status()
    return r.json().get("data", {}).get("objects", [{}])[0].get("data", []) or []

def _ensure_interfaces_slot(device):
    if 'interfaces' not in device or device['interfaces'] is None:
        device['interfaces'] = []
        
def _norm_status(v):
    if isinstance(v, int):
        return v
    s = str(v).strip().lower()
    if s == "up" or s == 'none': return 1
    if s == "down": return 2
    return None

def _merge_device_interfaces(device_list, device_id, rows):
    # Add/replace interface rows for a single device into device_list.
    # rows is a list of dicts from cdt_port: {id, name, deviceid, RxTxErrorPercent, ...}
    by_id = _index_by_id(device_list)
    dev = by_id.get(device_id)
    if not dev:
        return
    _ensure_interfaces_slot(dev)
    # Replace interfaces for this device (or you could merge selectively)
    dev['interfaces'] = []
    for p in rows or []:
        errors_ = p.get('RxTxErrorPercent', [{}]).get('total', [])
        errors = int(0 if errors_ is None else errors_)
        admin = _norm_status(p.get('ifAdminStatus'))
        oper  = _norm_status(p.get('ifOperStatus'))
        # Normalize field names across builds
        dev['interfaces'].append({
            'id': p.get('id'),
            'name': p.get('name'),
            'deviceid': p.get('deviceid') or p.get('device_id'),
            'RxTxErrorPercent': errors,
            'ifAdminStatus': admin,
            'ifOperStatus':  oper,
            'is_alerting': (admin == 1 and oper != 1) or errors > 1
        })

@transaction.atomic
def statseeker_persist_alerts(device_list, inv_by_ip, inv_by_name, include_if_down, include_if_errors, error_threshold):
    # device_list: (id, name, ipaddress, ping_state, interfaces=[...])
    # inv_by_ip/name: dicts mapping inventory (string IP/name) -> Inventory obj
    # error_threshold: float; if None, pulled from StatseekerSettings.error_pct_threshold
    now = timezone.now()
    created_cnt = 0
    updated_cnt = 0
    seen_keys = set()

    if error_threshold is None:
        error_threshold = float(getattr(error_threshold, 0) or 0)

    # helper to get the Inventory row for a device
    def _resolve_inventory(dev):
        dev_ip = str(dev.get("ipaddress") or "")
        dev_name = dev.get("name") or ""
        inv = inv_by_ip.get(dev_ip)
        if not inv:
            inv = inv_by_name.get(dev_name)
        return inv

    # upsert “current” alerts
    for dev in device_list:
        inv = _resolve_inventory(dev)

        # DEVICE_DOWN
        if str(dev.get("ping_state", "")).lower() != "up":
            k = (inv.pk if inv else None, "DEVICE_DOWN", "")
            seen_keys.add(k)
            c, u = _upsert_alert(inv, "DEVICE_DOWN", "", severity="critical",
                          metric_value=None, now=now)
            created_cnt += int(c)
            updated_cnt += int(u and not c)

        # INTERFACES
        for p in (dev.get("interfaces") or []):
            name = p.get("name") or ""
            admin_up = _is_admin_up(p.get("ifAdminStatus"))
            oper_up  = _is_up(p.get("ifOperStatus"))
            err_pct  = _as_decimal(p.get("RxTxErrorPercent"))

            # IF_DOWN
            if include_if_down and admin_up and not oper_up:
                k = (inv.pk if inv else None, "IF_DOWN", name)
                seen_keys.add(k)
                c, u = _upsert_alert(inv, "IF_DOWN", name, severity="major",
                              metric_value=None, now=now)
                created_cnt += int(c)
                updated_cnt += int(u and not c)

            # IF_ERRORS
            if include_if_errors and err_pct is not None and err_pct >= error_threshold:
                k = (inv.pk if inv else None, "IF_ERRORS", name)
                seen_keys.add(k)
                c, u = _upsert_alert(inv, "IF_ERRORS", name, severity="minor",
                              metric_value=err_pct, now=now)
                created_cnt += int(c)
                updated_cnt += int(u and not c)

    # Pull all active alerts for the devices we touched (or all, if inventory could be None)
    touched_device_ids = {inv.pk for inv in inv_by_ip.values()} | {inv.pk for inv in inv_by_name.values()}
    touched_device_ids.discard(None)

    active_qs = StatseekerAlert.objects.filter(active=True)
    if touched_device_ids:
        active_qs = active_qs.filter(device_id__in=touched_device_ids) | active_qs.filter(device__isnull=True)

    to_resolve = []
    resolved_cnt = 0
    for a in active_qs.select_related("device"):
        key = (a.device_id, a.alert_type, (a.interface_name or ""))
        if key not in seen_keys:
            a.active = False
            a.last_seen_at = now
            a.note = (a.note + "\nAuto-resolved by Statseeker collector").strip()
            to_resolve.append(a)
            resolved_cnt += 1

    if to_resolve:
        StatseekerAlert.objects.bulk_update(to_resolve, ["active", "last_seen_at", "note"])
        
    return {
        "created": created_cnt,
        "updated": updated_cnt,
        "resolved": resolved_cnt,
        "processed": len(seen_keys),
    }

def _upsert_alert(inv, alert_type, if_name, *, severity="", metric_value=None, now=None):
    now = now or timezone.now()
    mv = _to_decimal(metric_value)

    obj, created = StatseekerAlert.objects.get_or_create(
        device=inv,
        alert_type=alert_type,
        interface_name=if_name or "",
        active=True,
        defaults=dict(
            severity=severity or "",
            metric_value=mv,
            started_at=now,
            last_seen_at=now,
        ),
    )

    changed = False
    if not created:
        # update mutable fields if different
        updates = []
        if (severity or "") != obj.severity:
            obj.severity = severity or ""
            updates.append("severity")
        if mv is not None and obj.metric_value != mv:
            obj.metric_value = mv
            updates.append("metric_value")

        obj.last_seen_at = now
        updates.append("last_seen_at")

        if updates:
            obj.save(update_fields=updates)
            changed = True

    return created, changed

def statseeker_sync_alerts():
    cfg = StatseekerSettings.load()
    base = cfg.base_url.rstrip("/")
    auth = (cfg.credential.username, cfg.credential.password)
    verifySSL = cfg.verify_ssl
    token = _SScookie(base, auth, verifySSL)
    headers = { 'Accept': 'application/json', 'Content-Type': 'application/json', 'Authorization': f'Bearer {token}'}
    # tracked will be an list of objects of the tracked devices. each object has "priority_interfaces" which is comma-seperated.
    tracked = list(cfg.tracked_devices.select_related("site", "platform").all())
    inv_by_ip = {str(inv.ipaddress_mgmt): inv for inv in tracked if inv.ipaddress_mgmt}
    inv_by_name = {inv.name: inv for inv in tracked}
    querybase = 'api/latest/' # v2.1
  
    # DeviceList Dict. from Statseeker
    device_list = _build_device_ip_list(base, auth, headers, verifySSL, tracked)

    # ping state
    # https://statseeker/api/latest/cdt_device?fields=deviceid,ping_state&deviceid_filter=IS("6318048")
    # https://statseeker/api/latest/cdt_device?fields=deviceid,ping_state&deviceid_filter=IN("6318048","6318049")
    # Use "IN" if using multiple objects to filter, use "IS" if filtering a single object in the Statseeker API
    ping_state_json = _device_ping_state(base, auth, headers, verifySSL, device_list)
    _merge_ping_states(device_list, ping_state_json)

    # tracked interfaces (IFUP/IFDOWN/IFERROR)
    # https://statseeker/api/latest/cdt_port?fields=id,name,deviceid,ifAdminStatus,ifOperStatus,RxTxErrorPercent&RxTxErrorPercent_formats=total&deviceid_filter=IS("6318048")&name_filter=IN("Ethernet1/43","Ethernet2/43")

    # Place the Interface status and errors in device_list
    for dev in device_list:
        dev_ip = str(dev.get('ipaddress') or '')
        dev_name = dev.get('name') or ''
        inv = inv_by_ip.get(dev_ip)  # primary match on mgmt IP

        if not inv:
            inv = inv_by_name.get(dev_name)
    	# Save the tracked list onto the device dict (handy for debugging or templates)
        tracked_names = _tracked_interfaces(inv) if inv else []
        dev['tracked_interfaces'] = tracked_names

        if not tracked_names:
    		# Still create the interfaces slot so your structure is consistent
            _merge_device_interfaces(device_list, dev['id'], [])
            continue
    
    	# Fetch & merge the tracked ports for this device
        try:
            rows = _get_tracked_interfaces(base, auth, headers, verifySSL, dev['id'], tracked_names)
            _merge_device_interfaces(device_list, dev['id'], rows)

        except Exception as e:
    		# Don’t abort the entire sync if one device fails
            logger.exception(f"Statseeker: failed cdt_port for device {dev_name} ({dev_ip}) id={dev['id']}: {e}")
            _merge_device_interfaces(device_list, dev['id'], [])

    # Process Alerts w/ device_list
    stats = statseeker_persist_alerts(device_list, inv_by_ip, inv_by_name, cfg.include_if_down, cfg.include_if_errors, cfg.error_pct_threshold)

    return stats