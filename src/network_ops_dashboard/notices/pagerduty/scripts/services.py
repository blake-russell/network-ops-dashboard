import requests
import logging
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from network_ops_dashboard.notices.pagerduty.models import PagerDutySettings, PagerDutyIncident 

PD_BASE = "https://api.pagerduty.com"
logger = logging.getLogger('network_ops_dashboard.pagerduty')

def _dt_or_now(s):
    dt = parse_datetime(s) if isinstance(s, str) else s
    return dt or timezone.now()

def pd_sync_open_incidents():
    cfg = PagerDutySettings.load()

    if not cfg.enabled or not cfg.credential:
        return 0

    token = cfg.credential.api_key
    headers = {
        "Authorization": f"Token token={token}",
        "Accept": "application/vnd.pagerduty+json;version=2",
        "Content-Type": "application/json",
    }
    params = {
        "statuses[]": ["triggered", "acknowledged"],
        "limit": 100,
        "offset": 0,
        "total": "false",
    }
    if cfg.urgency_filter in ("high", "low"):
        params["urgencies[]"] = cfg.urgency_filter

    service_ids = [s.strip() for s in (cfg.service_ids_csv or "").split(",") if s.strip()]
    for sid in service_ids:
        params.setdefault("service_ids[]", []).append(sid)

    items = []
    session = requests.Session()
    session.verify = bool(cfg.verify_ssl)
    while True:
        resp = session.get(f"{PD_BASE}/incidents", headers=headers, params=params, timeout=20)
        resp.raise_for_status()
        data = resp.json()
        items.extend(data.get("incidents", []))
        if not data.get("more"):
            break
        params["offset"] = params.get("offset", 0) + params.get("limit", 100)

    # Upsert open incidents
    seen_ids = set()
    for it in items:
        iid = it["id"]
        seen_ids.add(iid)
        service = (it.get("service") or {})
        assigns = ", ".join([a.get("assignee", {}).get("summary", "") for a in it.get("assignments", []) if a.get("assignee")])
        obj, created = PagerDutyIncident.objects.get_or_create(
            incident_id=iid,
            defaults=dict(
                title=it.get("title") or "",
                status=it.get("status") or "",
                urgency=it.get("urgency") or "",
                service_name=service.get("summary") or "",
                service_id=service.get("id") or "",
                html_url=it.get("html_url") or "",
                created_at=_dt_or_now(it.get("created_at")),
                last_status_at=_dt_or_now(it.get("last_status_change_at")),
                active=True,
                summary=it.get("summary") or "",
                assignments=assigns,
            ),
        )
        changed = False
        for f, v in dict(
            title=it.get("title") or "",
            status=it.get("status") or "",
            urgency=it.get("urgency") or "",
            service_name=service.get("summary") or "",
            service_id=service.get("id") or "",
            html_url=it.get("html_url") or "",
            last_status_at=_dt_or_now(it.get("last_status_change_at")),
            active=True,
            summary=it.get("summary") or "",
            assignments=assigns,
        ).items():
            if getattr(obj, f) != v:
                setattr(obj, f, v); changed = True
        if changed:
            obj.synced_at = timezone.now()
            obj.save()

    # Mark any previously-open incidents that no longer appear as inactive (resolved)
    now = timezone.now()
    PagerDutyIncident.objects.filter(active=True).exclude(incident_id__in=seen_ids)\
        .update(active=False, last_status_at=now, synced_at=now)

    return len(seen_ids)
