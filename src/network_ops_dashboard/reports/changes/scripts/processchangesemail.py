import os
import email
from email import policy
from email.parser import BytesParser
from email.header import decode_header
import pandas as pd
from datetime import datetime, timedelta
import json
import re
from django.utils.timezone import make_aware
import logging
from network_ops_dashboard.models import SiteSecrets
from network_ops_dashboard.reports.changes.models import CompanyChanges

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

def ProcessChangesEmails():
    logger.info(f'ProcessChangesEmails Running.')
    try:
        changes_folder = SiteSecrets.objects.filter(varname='changes_folder')[0].varvalue
        changes_extract_folder = SiteSecrets.objects.filter(varname='changes_extract_folder')[0].varvalue
        os.makedirs(changes_extract_folder, exist_ok=True)
    except Exception as e:
        logger.exception(f"ProcessChangesEmails: No 'changes_folder' or 'changes_extract_folder' set in SiteSecrets.objects(): {e}")
        raise
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
                                    # Read Excel file, skipping to header row, filter next 7 days only
                                    df = pd.read_excel(out_path, skiprows=3)  # Header row begins on row 4. Edit this if necessary for your own format.
                                    df['Scheduled Start'] = pd.to_datetime(df['Scheduled Start'], errors='coerce')  # Handle parse errors safely
                                    today = datetime.today()
                                    next_7_days = today + timedelta(days=7)
                                    df = df[df['Scheduled Start'].between(today, next_7_days)] # Your spreadsheet column name might differ - change if necessary
                                    # Load location filter list from SiteSecrets to search "Location" Column in xlsx file
                                    valid_locations = json.loads(SiteSecrets.objects.get(varname="changes_valid_locations").varvalue)
                                    # Filter only valid locations
                                    df = df[df['Location'].isin(valid_locations)] # Your location column name might differ - change if necessary
                                    # Clear existing entries
                                    CompanyChanges.objects.all().delete()
                                    # Get dynamic field mapping from SiteSecrets
                                    column_map = json.loads(SiteSecrets.objects.get(varname="changes_column_map").varvalue)
                                    '''Create a SiteSecrets entry named "changes_column_map" with a json object to load like so:
                                    {
                                    "team_name": "Team Name",
                                    "change_id": "Change#",
                                    "start": "Scheduled Start",
                                    "end": "Scheduled End",
                                    "location": "Location",
                                    "summary": "Change Description",
                                    "reason": "Change Reason",
                                    "risk": "Risk Level"
                                    }
                                    Add as you see fit to customize the script as needed '''
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