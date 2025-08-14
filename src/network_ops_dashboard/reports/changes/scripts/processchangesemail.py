import os
from email import policy
from email.parser import BytesParser
from email.header import decode_header
import pandas as pd
from datetime import datetime, timedelta
import re
from django.utils.timezone import make_aware
from typing import List, Set
import logging
from network_ops_dashboard.inventory.models import Site
from network_ops_dashboard.reports.changes.models import CompanyChanges, CompanyChangesSettings

logger = logging.getLogger('network_ops_dashboard.changes')

def get_decoded_filename(part):
    filename = part.get_filename()
    if filename:
        decoded_parts = decode_header(filename)
        return ''.join(
            str(part[0], part[1] or 'utf-8') if isinstance(part[0], bytes) else part[0]
            for part in decoded_parts
        ).strip()
    return None

def safe_filename(name):
    return re.sub(r'[^a-zA-Z0-9_.-]', '_', name)

def make_serializable(value):
    if isinstance(value, pd.Timestamp):
        return value.isoformat()
    elif pd.isna(value):
        return None
    return str(value)

def _norm(s: str) -> str:
    return (s or "").strip().casefold()

def build_valid_locations(settings_obj) -> Set[str]:
    names = []

    if getattr(settings_obj, "use_sites_for_locations", False):
        chosen = list(settings_obj.sites_to_filter.all().values_list("name", flat=True))
        if chosen:
            names = chosen
        else:
            names = list(Site.objects.values_list("name", flat=True))
    else:
        custom = getattr(settings_obj, "custom_valid_locations", None) or []
        if custom:
            names = list(custom)
        else:
            names = list(Site.objects.values_list("name", flat=True))

    return set(_norm(n) for n in names if n)


def ProcessChangesEmails():
    logger.info(f'ProcessChangesEmails Running.')
    DEFAULT_COLUMN_MAP = {
        "team_name": "Team Name",
        "change_id": "Change#",
        "scheduled_start": "Scheduled Start",
        "scheduled_end": "Scheduled End",
        "class_type": "Change Class",
        "location": "Location",
        "summary": "Change Description",
        "reason": "Change Reason",
        "risk": "Risk Level",
        "group": "Assignment Group"
    }
    settings_obj, _ = CompanyChangesSettings.objects.get_or_create(pk=1)
    if not settings_obj.column_map:
        settings_obj.column_map = DEFAULT_COLUMN_MAP.copy()
        settings_obj.save()
    changes_folder = settings_obj.changes_folder
    changes_extract_folder = settings_obj.extract_folder
    skip_rows = settings_obj.header_row - 1
    days_before = settings_obj.days_ahead
    days_ahead = settings_obj.days_ahead
    column_map = settings_obj.column_map
    loc_col = settings_obj.column_map.get("location", "Location")
    start_col = settings_obj.column_map.get("scheduled_start", "Scheduled Start")
    for filename in os.listdir(changes_folder):
        file_path = os.path.join(changes_folder, filename)
        if os.path.isfile(file_path) and filename.endswith('.msg'):
            try:
                with open(file_path, 'rb') as email:
                    logger.info(f"ProcessChangesEmails: Processing {filename}.")
                    msg = BytesParser(policy=policy.default).parse(email)
                for part in msg.iter_attachments():
                    content_disposition = part.get("Content-Disposition", "")
                    if "attachment" in content_disposition:
                        fname = get_decoded_filename(part)
                        logger.info(f'ProcessChangesEmails: Checking attachment: {fname}')
                        if fname and fname.lower().endswith(".xlsx"):
                            safe_name = safe_filename(fname)
                            os.makedirs(changes_extract_folder, exist_ok=True)
                            out_path = os.path.join(changes_extract_folder, safe_name)
                            with open(out_path, 'wb') as fp:
                                payload = part.get_payload(decode=True)
                                if payload:
                                    fp.write(payload)
                                    logger.info(f'ProcessChangesEmails: Extracted: {out_path}')
                                    # Read Excel file, skipping to header row
                                    df = pd.read_excel(out_path, skiprows=skip_rows)
                                    df[start_col] = pd.to_datetime(df[start_col], errors='coerce')
                                    days_before = max(days_before or 1, 1)
                                    days_ahead = max(days_ahead or 7, 1)
                                    today = datetime.today()
                                    start_range = today - timedelta(days=days_before)
                                    end_range = today + timedelta(days=days_ahead)
                                    df = df[df[start_col].between(start_range, end_range)]
                                    # Filter only valid locations
                                    df["_loc_norm"] = df[loc_col].astype(str).str.strip().str.casefold()
                                    valid_locations = build_valid_locations(settings_obj)
                                    df = df[df["_loc_norm"].isin(valid_locations)]
                                    df = df.drop(columns=["_loc_norm"])
                                    # Clear existing entries
                                    CompanyChanges.objects.all().delete()
                                    # Get known model fields dynamically
                                    model_fields = [
                                        field.name for field in CompanyChanges._meta.get_fields()
                                        if not field.is_relation and field.name not in ('id', 'imported_at', 'metadata')
                                    ]
                                    # Create new entries
                                    for _, row in df.iterrows():
                                        kwargs = {}
                                        metadata = {}
                                        for col_name in row.index:
                                            if col_name not in column_map.values():
                                                metadata[col_name] =  make_serializable(row.get(col_name, ''))
                                        for internal_field, column_name in column_map.items():
                                            value = row.get(column_name, '')
                                            if internal_field in model_fields:
                                                kwargs[internal_field] = value
                                            else:
                                                metadata[internal_field] = value
                                        CompanyChanges.objects.create(**kwargs, metadata=metadata)
                                    logger.info(f'ProcessChangesEmails: Imported {len(df)} company change(s).')
                                else:
                                    logger.info(f'ProcessChangesEmails: No Payload in : {safe_name}')
                os.remove(file_path)
                os.remove(out_path)
            except Exception as e:
                logger.exception(f'ProcessChangesEmails: Failed to r/w email and xlsx file: {filename}: {e}')
                raise