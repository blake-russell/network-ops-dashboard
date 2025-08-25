from crontab import CronTab
from django.conf import settings
from typing import Optional
import getpass, shutil, logging

log = logging.getLogger(__name__)

COLLECTORS = {
    "asa_vpn_stats": "collect_asa_vpn_stats",
    "process_emails": "process_emails",
    "send_oncall_email": "send_oncall_email",
    "archive_oncall_closed": "archive_oncall_closed",
    "sdwan_vmanage_stats": "collect_sdwan_stats",
    "pagerduty_incidents": "collect_pd_incidents",
}

def _job_comment(key: str) -> str:
    return f"network_ops_dashboard:{key}"

def _job_command(command_name: str) -> str:
    return f"{settings.PYTHON_BIN} {settings.MANAGE_PY} {command_name}"

def _target_user(user: Optional[str]) -> Optional[str]:
    # Let settings override the OS user we write crontab for
    return getattr(settings, "CRON_USER", None) or user

def ensure_minutely_cron(key: str, user: Optional[str] = None) -> None:
    if key not in COLLECTORS:
        raise ValueError(f"Unknown collector key: {key}")
    comment = _job_comment(key)
    cmd = _job_command(COLLECTORS[key])

    os_user = _target_user(user)
    crontab_bin = shutil.which("crontab")
    log.info("CRON ensure start: key=%s user=%s proc_user=%s crontab_bin=%s cmd=%s",
             key, os_user, getpass.getuser(), crontab_bin, cmd)

    try:
        cron = CronTab(user=os_user)
        jobs = [j for j in cron if j.comment == comment]
        if jobs:
            for j in jobs:
                j.setall("* * * * *")
                j.set_command(cmd)
            cron.write()
        else:
            job = cron.new(command=cmd, comment=comment)
            job.setall("* * * * *")
            cron.write()

        current = [f"{j.slices} {j.command}  # {j.comment}" for j in cron]
        log.info("CRON ensure done. Entries for user=%s:\n%s",
                 os_user or getpass.getuser(), "\n".join(current) or "(empty)")

    except Exception as e:
        log.exception("CRON ensure failed for user=%s: %s", os_user, e)
        raise

def ensure_daily_cron(key: str, hhmm: str, user: Optional[str] = None) -> None:
    """Ensure one daily cron at HH:MM (24h)."""
    if key not in COLLECTORS:
        raise ValueError(f"Unknown collector key: {key}")
    
    try:
        h, m = map(int, hhmm.split(":"))
        assert 0 <= h <= 23 and 0 <= m <= 59
    except Exception:
        raise ValueError(f"Invalid time '{hhmm}', expected 'HH:MM'")
    comment = _job_comment(key)
    cmd = _job_command(COLLECTORS[key])
    os_user = _target_user(user)
    cron = CronTab(user=os_user)
    jobs = [j for j in cron if j.comment == comment]
    if jobs:
        for j in jobs:
            j.setall(f"{m} {h} * * *")
            j.set_command(cmd)
        cron.write()
        return
    job = cron.new(command=cmd, comment=comment)
    job.setall(f"{m} {h} * * *")
    cron.write()

def ensure_weekly_cron(key: str, hhmm: str, weekday: int, user: Optional[str] = None) -> None:
    """Install/normalize a once-per-week cron at HH:MM on weekday(0=Sun..6=Sat)."""
    if key not in COLLECTORS:
        raise ValueError(f"Unknown key: {key}")
    h, m = map(int, hhmm.split(":"))
    d = int(weekday) % 7  # safety
    os_user = _target_user(user)
    cron = CronTab(user=os_user)
    comment = _job_comment(key)
    cmd = _job_command(COLLECTORS[key])
    cron.remove_all(comment=comment)
    job = cron.new(command=cmd, comment=comment)
    # crontab uses 0=Sun..6=Sat; our default uses 0=Mon..6=Sun → remap:
    crontab_dow = (d + 1) % 7
    job.setall(f"{m} {h} * * {crontab_dow}")
    cron.write()
    log.info("Installed weekly cron %s at %02d:%02d weekday=%d", key, h, m, d)
    
def remove_cron(key: str, user: Optional[str] = None) -> None:
    if key not in COLLECTORS:
        raise ValueError(f"Unknown collector key: {key}")
    os_user = _target_user(user)
    log.info("CRON remove start: key=%s user=%s", key, os_user)
    cron = CronTab(user=os_user)
    cron.remove_all(comment=_job_comment(key))
    cron.write()
    log.info("CRON remove done.")