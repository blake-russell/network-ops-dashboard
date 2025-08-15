# network_ops_dashboard/scripts/cron.py
from crontab import CronTab
from django.conf import settings
from typing import Optional
import getpass, shutil, logging

log = logging.getLogger(__name__)

COLLECTORS = {
    "asa_vpn_stats": "collect_asa_vpn_stats",
    "process_emails": "process_emails",
    "send_oncall_email": "send_oncall_email",
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
        cron = CronTab(user=os_user)  # None = current process user
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

        # Dump resulting crontab to logs
        current = [f"{j.slices} {j.command}  # {j.comment}" for j in cron]
        log.info("CRON ensure done. Entries for user=%s:\n%s",
                 os_user or getpass.getuser(), "\n".join(current) or "(empty)")

    except Exception as e:
        log.exception("CRON ensure failed for user=%s: %s", os_user, e)
        raise

def ensure_daily_cron(key: str, hhmm: str) -> None:
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
    cron = CronTab(user=True)
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
    
def remove_cron(key: str, user: Optional[str] = None) -> None:
    if key not in COLLECTORS:
        raise ValueError(f"Unknown collector key: {key}")
    os_user = _target_user(user)
    log.info("CRON remove start: key=%s user=%s", key, os_user)
    cron = CronTab(user=os_user)
    cron.remove_all(comment=_job_comment(key))
    cron.write()
    log.info("CRON remove done.")