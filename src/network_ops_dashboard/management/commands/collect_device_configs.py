from django.core.management.base import BaseCommand
from django.core.mail import send_mail
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = "Collect Inventory Device Configs."

    @staticmethod
    def _email_config_backup_summary(results, cfg):
        total = len(results)
        failed = [r for r in results if not r.get("success")]
        passed = [r for r in results if r.get("success")]
        subject = "[Config Backup] All Successful" if not failed else f"[Config Backup] {len(failed)} Failures"

        results_str = f"Processed {total} device config backups and {len(failed)} failed."
        lines = [results_str, ""]

        ordered = failed + passed
        for r in ordered:
            if r.get("success"):
                lines.append(f"{r['device']}: OK")
            else:
                err = r.get("error")
                lines.append(f"{r['device']}: FAILED" + (f" — {err}" if err else ""))

        body = "\n".join(lines) + "\n"

        to_email = getattr(cfg, "alert_email", "") or getattr(settings, "ADMINS", [("", "")])[0][1] or None
        if to_email:
            send_mail(
                subject,
                body,
                getattr(settings, "DEFAULT_FROM_EMAIL", None),
                [to_email],
                fail_silently=True,
            )

    def handle(self, *args, **kwargs):
        from network_ops_dashboard.inventory.models import ConfigBackupSchedule
        from network_ops_dashboard.inventory.scripts.services import pull_device_config

        cfg = ConfigBackupSchedule.objects.first()
        if not cfg:
            logger.warning("Config Backup: no ConfigBackupSchedule found.")
            return
        if not cfg.enabled:
            logger.info("Config Backup: disabled; skipping.")
            return
        if not cfg.devices.exists():
            logger.info("Config Backup: no devices enabled for config backup; skipping.")
            return

        results = []
        logger.info("Config Backup: Backups started.")

        for device in cfg.devices.all():
            try:
                pull_device_config(device)
                results.append({"device": device.name, "success": True})
                logger.info(f"Config Backup: {device.name} backup success.")
            except Exception as e:
                results.append({"device": device.name, "success": False})
                logger.error(f"Config Backup: {device.name} backup failed: {e}")

        failed = [r for r in results if not r["success"]]
        logger.info(f"Config Backup: Finished. {len(results)} processed, {len(failed)} failed.")

        if cfg.email_alerts:
            if cfg.alert_email:
                try:
                    self._email_config_backup_summary(results, cfg)
                    logger.info("Config Backup: Summary email sent.")
                except Exception as e:
                    logger.error(f"Config Backup: Email failed: {e}")
            else:
                logger.info(f"Config Backup: Email Alerts enabled but no email configured. Please configure email address in settings.")