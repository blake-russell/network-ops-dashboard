import os
import logging
import re
from network_ops_dashboard.models import SiteSecrets
from network_ops_dashboard.reports.windstream.models import *

logger = logging.getLogger('network_ops_dashboard.windstream')

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

def extract_ids_from_email(email_body, circuit_id_lookup):
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

def ProcessWindstreamEmails(circuit_id_list):
    logger.info(f"WindstreamMtcEmail Running.")
    impact_type_list = ['Outage', 'Switch Hit']
    excluded_status = ['Cancelled', 'Archived', 'Auto-Archived', 'Auto-Archived-Cktid', 'Completed']
    try:
        wstmtcemails_folder = SiteSecrets.objects.filter(varname='wstmtcemails_folder')[0].varvalue
    except Exception as e:
        logger.exception(f"No 'wstmtcemails_folder' set in SiteSecrets.objects(): {e}")
        raise
    for filename in os.listdir(wstmtcemails_folder):
        file_path = os.path.join(wstmtcemails_folder, filename)
        if os.path.isfile(file_path) and filename.endswith('.msg'):
            try:
                with open(file_path, 'r', encoding = "ISO-8859-1") as email:
                    #split the email
                    content1 = email.read()
                    content2 = content1.split('.png> \n\n\n')[-1]
                    content = content2.split('\n\n\nIf you experience')[0].strip()
                    normalized_content = content.replace('\t', ' ')
                    #regex match any valid circuit IDs in the email body
                    matches = extract_ids_from_email(normalized_content, circuit_id_list)
                    #validate it is an email with a cktid we care about
                    if matches:
                        #start parsing out wmt, status, impact, datetimes
                        wmt1 = content.split('WMT:')[-1]
                        wmt2 = wmt1.split('\nMaintenance Address')[0].strip()
                        status1 = content.split('\s')[-1]
                        status2 = status1.split('Maintenance')[0].strip()
                        impact_list = []
                        impact1 = content.split('Impact End\n')[-1]
                        impact2 = impact1.split('Note:')[0]
                        for impact_type in impact_type_list:
                            if impact2.find(impact_type):
                                impact_list.append(impact_type)
                        impact_str = ', '.join(impact_list)
                        startdatetime1 = content.split('Event Start Date & Time:')[-1]
                        startdatetime2 = startdatetime1.split('\nEvent')[0].strip()
                        enddatetime1 = content.split('Event End Date & Time:')[-1]
                        enddatetime2 = enddatetime1.split('\nImpact')[0].strip()
                        wmt_entry_qs = WindstreamMtcEmail.objects.filter(wmt=wmt2)
                        if wmt_entry_qs.exists():
                            #if entry with wmt# already exists then update what has changed
                            wmt_entry = wmt_entry_qs.first()
                            if wmt_entry.status not in excluded_status:
                                #only make updates if wmt has not been cancelled, completed, or archived
                                wmt_entry.status = status2
                                wmt_entry.impact = impact_str
                                wmt_entry.startdatetime=startdatetime2
                                wmt_entry.enddatetime=enddatetime2
                                wmt_entry.save()
                                for raw, circuit_obj in matches:
                                    try:
                                        logger.info(f"WindstreamMtcEmail WMT: {wmt2} trying to add {circuit_obj}.")
                                        wmt_entry.cktid.add(circuit_obj)
                                    except Exception as e:
                                        logger.exception(f"Error trying add {circuit_obj} to {wmt2}: {e}")
                                logger.info(f"WindstreamMtcEmail WMT: {wmt2} updated to {status2}.")
                        else:
                            #if entry with wmt# does not exist then create a new object entry
                            wmt_entry = WindstreamMtcEmail.objects.create(
                                wmt=wmt2,
                                status=status2,
                                impact=impact_str,
                                startdatetime=startdatetime2,
                                enddatetime=enddatetime2
                            )
                            for raw, circuit_obj in matches:
                                try:
                                    logger.info(f"WindstreamMtcEmail WMT: {wmt2} adding {circuit_obj}.")
                                    wmt_entry.cktid.add(circuit_obj)
                                except Exception as e:
                                    logger.exception(f"Error trying add {circuit_obj} to new {wmt2}: {e}")
                            logger.info(f"WindstreamMtcEmail new WMT: {wmt2} created.")
                    else:
                        try:
                            #figure out if the WMT has been updated with valid circuit ID removed then auto-archive it
                            wmt1 = content.split('WMT:')[-1]
                            wmt2 = wmt1.split('\nMaintenance Address')[0].strip()
                            wmt_entry_qs = WindstreamMtcEmail.objects.filter(wmt=wmt2)
                            if wmt_entry_qs.exists():
                                wmt_entry = wmt_entry_qs.first()
                                if wmt_entry.status not in excluded_status:
                                    wmt_entry.status = 'Auto-Archived-Cktid'
                                    wmt_entry.save()
                                    logger.info(f"WindstreamMtcEmail WMT: {wmt2} updated to Auto-Archived-Cktid (No valid circuit id found).")
                        except Exception as e:
                            logger.exception(f"Error trying wmt: {e}")
                            continue
                os.remove(file_path)
            except Exception as e:
                logger.exception(f"Error reading {filename}: {e}")
                continue