import os
import logging
import re
import base64
# from datetime import datetime
from email import policy
from email.parser import BytesParser
from network_ops_dashboard.reports.circuits.models import *

logger = logging.getLogger('network_ops_dashboard.circuits')

def cktid_to_repattern(cktid):
    cktid = cktid.strip()
    parts = cktid.split('/')
    parts = [re.escape(p.strip()) for p in parts if p.strip()]
    # Allow any whitespace (\s matches tabs, spaces, newlines)
    pattern = r'\s*/\s*'.join(parts)
    # Optional trailing separator (e.g., final slash or slash with space)
    pattern = rf'\s*{pattern}\s*/?\s*'
    return pattern

def normalize_circuit_id(s):
    # Remove all slashes and whitespace
    return re.sub(r'[\s/]+', '', s).upper()

def extract_ids_from_email_windstream(email_body, circuit_id_lookup):
    # Match starts with expected prefixes (IP/ WS/ WA/ or 2-digit like 58/)
    prefix_pattern = r'(?:IP|WS|WA|\d{2})'
    # Match 3 to 6 slash-separated parts (optionally space-padded)
    # Each part is alphanum/spaces, up to 10 chars
    segment = r'[A-Z0-9 ]{0,12}'
    sep = r'\s*/\s*'
    # Build full regex pattern
    pattern = rf'({prefix_pattern}{sep}{segment}{sep}{segment}(?:{sep}{segment}){{0,3}}{sep}?)'
    raw_candidates = re.findall(pattern, email_body, re.IGNORECASE)
    matches = []
    for raw in raw_candidates:
        norm = normalize_circuit_id(raw)
        if norm in circuit_id_lookup:
            matches.append((raw.strip(), circuit_id_lookup[norm]))
    return matches

def extract_ids_from_email_cogent(email_body, circuit_id_lookup):
    # Match starts with expected prefixes (3- followed by 6-12 digits)
    # Change this pattern below to match your own specific needs
    pattern = r'\b3-\d{6,12}\b'
    raw_candidates = re.findall(pattern, email_body, re.IGNORECASE)
    matches = []
    for raw in raw_candidates:
        norm = normalize_circuit_id(raw)
        if norm in circuit_id_lookup:
            matches.append((raw.strip(), circuit_id_lookup[norm]))
    return matches

def process_windstream(wstmtcemails_folder, circuit_id_list):
    # Parse Windstream email
    impact_type_list = [['Outage', r'(^|\s)Outage(\s|$)'], ['Switch Hit', r'(^|\s)Switch Hit(\s|$)']]
    excluded_status = ['Cancelled', 'Archived', 'Auto-Archived', 'Auto-Archived-Cktid', 'Completed']
    for filename in os.listdir(wstmtcemails_folder):
        file_path = os.path.join(wstmtcemails_folder, filename)
        if os.path.isfile(file_path) and filename.endswith('.msg'):
            try:
                with open(file_path, 'r', encoding="ISO-8859-1") as email:
                    # split the email
                    logger.info(f"ProcessCircuitMtcEmails: Processing Windstream Emails {filename}.")
                    content1 = email.read()
                    # content2 = content1.split('.png> \n\n\n')[-1] # VBScript Forwarding format
                    content2 = content1.split('.png]\n\n')[-1] # PowerAutomate Forwarding format
                    content = content2.split('\n\n\nIf you experience')[0].strip()
                    normalized_content = content.replace('\t', ' ')
                    # regex match any valid circuit IDs in the email body
                    matches = extract_ids_from_email_windstream(normalized_content, circuit_id_list)
                    # validate it is an email with a cktid we care about
                    if matches:
                        # start parsing out wmt, status, impact, datetimes
                        wmt1 = content.split('WMT:')[-1]
                        wmt2 = wmt1.split('\nMaintenance Address')[0].strip()
                        status1 = content.split('\s')[-1] # noqa: W605
                        status2 = status1.split('Maintenance')[0].strip()
                        impact_list = []
                        # impact1 = content.split('Impact End\t')[-1] # VBScript Forwarding format
                        impact1 = content.split('Impact End\n')[-1] # PowerAutomate Forwarding format
                        impact2 = impact1.split('Note:')[0]
                        for impact_type in impact_type_list:
                            if re.search(impact_type[1], impact2, re.IGNORECASE):
                                impact_list.append(impact_type[0])
                        impact_str = ', '.join(impact_list)
                        startdatetime1 = content.split('Event Start Date & Time:')[-1]
                        startdatetime2 = startdatetime1.split('\nEvent')[0].strip()
                        # startdatetime2_dt = datetime.strptime(startdatetime2.replace(', ', ' '), "%m/%d/%y %H:%M")
                        enddatetime1 = content.split('Event End Date & Time:')[-1]
                        enddatetime2 = enddatetime1.split('\nImpact')[0].strip()
                        # enddatetime2_dt = datetime.strptime(enddatetime2.replace(', ', ' '), "%m/%d/%y %H:%M")
                        wmt_entry_qs = CircuitMtcEmail.objects.filter(mtc_id=wmt2)
                        if wmt_entry_qs.exists():
                            # if entry with wmt# already exists then update what has changed
                            wmt_entry = wmt_entry_qs.first()
                            if wmt_entry.status not in excluded_status:
                                # only make updates if wmt has not been cancelled, completed, or archived
                                wmt_entry.status = status2
                                wmt_entry.impact = impact_str
                                wmt_entry.startdatetime = startdatetime2
                                wmt_entry.enddatetime = enddatetime2
                                wmt_entry.save()
                                for raw, circuit_obj in matches:
                                    try:
                                        logger.info(f"ProcessCircuitMtcEmails: Windstream#{wmt2} adding circuit {circuit_obj}.")
                                        wmt_entry.circuits.add(circuit_obj)
                                    except Exception as e:
                                        logger.exception(f"ProcessCircuitMtcEmails: Error trying add {circuit_obj} to Windstream#{wmt2}: {e}")
                                logger.info(f"ProcessCircuitMtcEmails: Windstream#{wmt2} updated to {status2}.")
                        else:
                            # if entry with wmt# does not exist then create a new object entry
                            wmt_entry = CircuitMtcEmail.objects.create(
                                mtc_id=wmt2,
                                status=status2,
                                impact=impact_str,
                                startdatetime=startdatetime2,
                                enddatetime=enddatetime2
                            )
                            for raw, circuit_obj in matches:
                                try:
                                    logger.info(f"ProcessCircuitMtcEmails: Windstream#{wmt2} adding circuit {circuit_obj}.")
                                    wmt_entry.circuits.add(circuit_obj)
                                except Exception as e:
                                    logger.exception(f"ProcessCircuitMtcEmails: Error trying add {circuit_obj} to new Windstream#{wmt2}: {e}")
                            logger.info(f"ProcessCircuitMtcEmails: New Windstream#{wmt2} created.")
                    else:
                        try:
                            # figure out if the WMT has been updated with valid circuit ID removed then auto-archive it
                            wmt1 = content.split('WMT:')[-1]
                            wmt2 = wmt1.split('\nMaintenance Address')[0].strip()
                            wmt_entry_qs = CircuitMtcEmail.objects.filter(mtc_id=wmt2)
                            if wmt_entry_qs.exists():
                                wmt_entry = wmt_entry_qs.first()
                                if wmt_entry.status not in excluded_status:
                                    wmt_entry.status = 'Auto-Archived-Cktid'
                                    wmt_entry.save()
                                    logger.info(f"ProcessCircuitMtcEmails: Windstream#{wmt2} updated to Auto-Archived-Cktid (No valid circuit id found).")
                        except Exception as e:
                            logger.exception(f"ProcessCircuitMtcEmails: Error trying Windstream#{wmt2}: {e}")
                            continue
                os.remove(file_path)
            except Exception as e:
                logger.exception(f"ProcessCircuitMtcEmails: Error reading {filename}: {e}")
                continue
    return None

def process_cogent(folder_path, circuit_id_list):
    # Parse Cogent email
    excluded_status = ['Cancellation', 'Archived', 'Auto-Archived', 'Auto-Archived-Cktid', 'Completed']
    # Status Patterns
    STATUS_PATTERNS = [
    ("Completed", re.compile(r"\b(maintenance\s+completed|completed\s+maintenance)\b", re.I)),
    ("Emergency", re.compile(r"\bemergency\b", re.I)),
    ("Planned",   re.compile(r"\bplanned\b", re.I)),
    # Fallback if "Planned" isn't present
    ("Planned",   re.compile(r"\bcircuit\s+provider\s+maintenance\b", re.I)),
    ]
    def _classify_subject(subject: str):
        status = "Unknown"
        for label, rx in STATUS_PATTERNS:
            if rx.search(subject or ""):
                status = label
                break
        return {"status": status}
    for filename in os.listdir(folder_path):
        file_path = os.path.join(folder_path, filename)
        if os.path.isfile(file_path) and filename.endswith('.msg'):
            try:
                with open(file_path, 'rb') as email:
                    encoded_content = BytesParser(policy=policy.default).parse(email)
                    for part in encoded_content.walk():
                        content_type = part.get_content_type()
                        # content_disposition = part.get("Content-Disposition", "")
                        content_transfer_encoding = part.get("Content-Transfer-Encoding", "").lower()
                        # Look for text parts that are base64 encoded
                        if content_type in ["text/plain", "text/html"]:
                            payload = part.get_payload()  # this will still be base64 encoded
                            if content_transfer_encoding == "base64":
                                try:
                                    decoded_bytes = base64.b64decode(payload)
                                    decoded_content = decoded_bytes.decode(part.get_content_charset() or 'utf-8', errors='replace')
                                except Exception as e:
                                    logger.exception(f"ProcessCircuitMtcEmails: Failed to decode email {filename}: {e}")
                                    raise
                            elif content_transfer_encoding == "quoted-printable":
                                from quopri import decodestring
                                decoded_content = decodestring(payload).decode(part.get_content_charset() or 'utf-8', errors='replace')
                            else:
                                decoded_content = payload
                                logger.info(f"ProcessCircuitMtcEmails: text/plain Cogent email passed: {filename}")
                        else:
                            decoded_content = payload
                            logger.info(f"ProcessCircuitMtcEmails: Encoded non text/plain Cogent email passed: {filename}")
                    # split the email
                    logger.info(f"ProcessCircuitMtcEmails: Processing Cogent Emails {filename}.")
                    content0 = decoded_content.replace('\\n', '').replace('=', '')
                    content1 = content0.split('Subject: [EXTERNAL]:')[1]
                    content = content1.split('We appreciate your patience ')[0]
                    subject = content.split('External')[0].strip()
                    # regex match any valid circuit IDs in the email body
                    matches = extract_ids_from_email_cogent(subject, circuit_id_list)
                    # validate it is an email with a cktid we care about
                    if matches:
                        try:
                            mtc_or_cancel_subject = subject.split('Importance')[0].strip()
                        except ValueError:
                            mtc_or_cancel_subject = subject.split(' ')[0].strip()
                        if mtc_or_cancel_subject.split(' ')[0] == "CANCELLATION":
                            mtc_id = mtc_or_cancel_subject.split(' ')[1].strip()
                            status = 'CANCELLATION'
                            ckt_number1 = mtc_or_cancel_subject.split(' - ')[1].strip()
                            ckt_number = ckt_number1.split(', ')
                            start_time1 = content.split('will not take place on ')[1].strip()
                            start_time2 = start_time1.split(' -')[0].strip()
                            # start_time_dt = datetime.strptime(start_time2.replace(' at ', ' '), "%m/%d/%y %H:%M")
                            start_time_str = start_time2.replace(' at ', ', ')
                            # end_time_dt = start_time_dt
                            end_time_str = start_time_str
                            impact_str = 'No impact unless rescheduled'
                        else:
                            mtc_id = mtc_or_cancel_subject.split(' ')[0].strip()
                            status = _classify_subject(mtc_or_cancel_subject)['status']
                            ckt_number1 = mtc_or_cancel_subject.split(' - ')[1].strip()
                            ckt_number = ckt_number1.split(', ')
                            start_time1 = content.split('Start time: ')[1].strip()
                            start_time2 = start_time1.split(' -')[0].strip()
                            # start_time_dt = datetime.strptime(start_time2.replace(' at ', ' '), "%m/%d/%y %H:%M")
                            start_time_str = start_time2.replace(' at ', ', ')
                            end_time1 = content.split('End time: ')[1].strip()
                            end_time2 = end_time1.split(' -')[0].strip()
                            # end_time_dt = datetime.strptime(end_time2.replace(' at ', ' '), "%m/%d/%y %H:%M")
                            end_time_str = end_time2.replace(' at ', ', ')
                            impact1 = content.split('Your Cogent services received at:')[0].strip()
                            if len(impact1) < 2:
                                impact1 = content.split('You Cogent services received at:')[0].strip()
                            impact_str = impact1.split('Expected Outage/Downtime: ')[1].strip()
                        ckt_id_list = []
                        for id in ckt_number:
                            ckt_id_list.append(id)
                        entry_qs = CircuitMtcEmail.objects.filter(mtc_id=mtc_id)
                        if entry_qs.exists():
                            # if entry with mtc_id# already exists then update what has changed
                            mtc_entry = entry_qs.first()
                            if mtc_entry.status not in excluded_status:
                                #  only make updates if mtc_id# has not been cancelled, completed, or archived
                                mtc_entry.status = status
                                if status != 'CANCELLATION':
                                    mtc_entry.impact = impact_str
                                    mtc_entry.startdatetime = start_time_str
                                    mtc_entry.enddatetime = end_time_str
                                mtc_entry.save()
                                for raw, circuit_obj in matches:
                                    try:
                                        logger.info(f"ProcessCircuitMtcEmails: Cogent#{mtc_id} adding circuit {circuit_obj}.")
                                        mtc_entry.circuits.add(circuit_obj)
                                    except Exception as e:
                                        logger.exception(f"ProcessCircuitMtcEmails: Error trying add {circuit_obj} to Cogent#{mtc_id}: {e}")
                                logger.info(f"ProcessCircuitMtcEmails: Cogent#{mtc_id} updated to {status}.")
                        else:
                            # if entry with mtc_id# does not exist then create a new object entry
                            mtc_entry = CircuitMtcEmail.objects.create(
                                mtc_id=mtc_id,
                                status=status,
                                impact=impact_str,
                                startdatetime=start_time_str,
                                enddatetime=end_time_str
                            )
                            for raw, circuit_obj in matches:
                                try:
                                    logger.info(f"ProcessCircuitMtcEmails: Cogent#{mtc_id} adding circuit {circuit_obj}.")
                                    mtc_entry.circuits.add(circuit_obj)
                                except Exception as e:
                                    logger.exception(f"ProcessCircuitMtcEmails: Error trying add {circuit_obj} to new Cogent#{mtc_id}: {e}")
                            logger.info(f"ProcessCircuitMtcEmails: New Cogent#{mtc_id} created.")
                    else:
                        try:
                            # figure out if the mtc_id has been updated with valid circuit ID removed then auto-archive it
                            mtc_id = subject.split(' ')[0].strip()
                            entry_qs = CircuitMtcEmail.objects.filter(mtc_id=mtc_id)
                            if entry_qs.exists():
                                mtc_entry = entry_qs.first()
                                if mtc_entry.status not in excluded_status:
                                    mtc_entry.status = 'Auto-Archived-Cktid'
                                    mtc_entry.save()
                                    logger.info(f"ProcessCircuitMtcEmails: Cogent#{mtc_id} updated to Auto-Archived-Cktid (No valid circuit id found).")
                        except Exception as e:
                            logger.exception(f"ProcessCircuitMtcEmails: Error trying Cogent#{mtc_id}: {e}")
                            continue
                os.remove(file_path)
            except Exception as e:
                logger.exception(f"ProcessCircuitMtcEmails: Error reading {filename}: {e}")
                continue
    return None

# Expand process handlers if needed