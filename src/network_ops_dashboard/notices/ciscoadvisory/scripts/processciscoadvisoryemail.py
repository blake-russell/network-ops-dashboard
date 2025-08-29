import os
import base64
import re
import logging
from django.utils import timezone
from datetime import datetime, date
from typing import Optional, List, Dict
from email import policy
from email.parser import BytesParser
from bs4 import BeautifulSoup
from typing import Tuple
from email.message import Message
from network_ops_dashboard.models import *
from network_ops_dashboard.notices.ciscoadvisory.models import *

logger = logging.getLogger('network_ops_dashboard.ciscoadvisory')

def _clean_text(s):
    if not s:
        return ""
    s = s.replace('\xa0', ' ').replace('Â', ' ')
    return re.sub(r'\s+', ' ', s).strip()

def _norm_label(s):
    s = _clean_text(s).rstrip(':')
    return s.lower()

def _parse_date(s):
    s = _clean_text(s)
    for fmt in ("%d-%b-%Y", "%Y-%m-%d", "%b %d, %Y"):
        try:
            return datetime.strptime(s, fmt).date()
        except ValueError:
            pass
    return timezone.now().date()

def _first_href_in(el):
    a = el.find("a")
    if a and a.has_attr("href"):
        return a["href"]
    return None

def read_html_from_message(fp):
    msg = BytesParser(policy=policy.default).parse(fp)
    best = None
    for part in msg.walk():
        ctype = part.get_content_type()
        if ctype == "text/html":
            best = part
            break
        if ctype == "text/plain" and best is None:
            best = part
    if not best:
        return None
    try:
        return best.get_content()
    except Exception as e:
        logger.exception("ProcessCiscoAdvisoryEmails: Failed to extract content: %s", e)
        return None

def extract_advisory_blocks(html):
    soup = BeautifulSoup(html, "html.parser")
    blocks = []

    h3s = soup.find_all("h3")
    if not h3s:
        for tab in soup.find_all("table"):
            block = _parse_advisory_table(None, tab)
            if block:
                blocks.append(block)
        return blocks

    for h3 in h3s:
        short_title = _clean_text(h3.get_text())
        table = h3.find_next("table")
        if not table:
            continue
        block = _parse_advisory_table(short_title, table)
        if block:
            blocks.append(block)

    return blocks

def _parse_advisory_table(short_title, table):
    rows = table.find_all("tr")
    data = {
        "short_title": short_title or "",
        "long_title": "",
        "long_title_url": None,
        "impact_rating": "Unknown",
        "description": "",
        "date": timezone.now().date(),
    }

    for r in rows:
        tds = r.find_all("td")
        if len(tds) < 2:
            continue
        label = _norm_label(tds[0].get_text())
        value_td = tds[1]

        if label.startswith("title"):
            a = value_td.find("a")
            data["long_title"] = _clean_text(a.get_text()) if a else _clean_text(value_td.get_text())
            if a and a.has_attr("href"):
                data["long_title_url"] = a["href"]
            if not data["short_title"]:
                data["short_title"] = data["long_title"][:100]
        elif label.startswith("impact"):
            data["impact_rating"] = _clean_text(value_td.get_text())
        elif label.startswith("description"):
            data["description"] = _clean_text(' '.join(value_td.stripped_strings))
            if not data["long_title_url"]:
                href = None
                for a in value_td.find_all("a", href=True):
                    if "CiscoSecurityAdvisory" in a["href"]:
                        href = a["href"]
                        break
                data["long_title_url"] = href or _first_href_in(value_td)
        elif label.startswith("date"):
            data["date"] = _parse_date(value_td.get_text())

    if not data["short_title"] and not data["long_title"]:
        return None
    return data

def save_blocks(blocks):
    created = 0
    for b in blocks:
        title_short = b.get("short_title") or (b.get("long_title") or "")[:100]
        dt = b.get("date") or timezone.now().date()
        defaults = dict(
            title=b.get("long_title") or title_short,
            impact_rating=b.get("impact_rating") or "Unknown",
            description=b.get("description") or "",
            url=b.get("long_title_url") or "",
            date=dt,
            status="Open",
        )
        obj, made = CiscoAdvisory.objects.get_or_create(
            title_short=title_short,
            date=dt,
            defaults=defaults,
        )
        if not made:
            changed = False
            for f, v in defaults.items():
                if v and getattr(obj, f) != v:
                    setattr(obj, f, v)
                    changed = True
            if changed:
                obj.save()
        else:
            created += 1
            logger.info("ProcessCiscoAdvisoryEmails: Created %s (%s)", title_short, dt)
    return created


def ProcessCiscoAdvisoryEmails():
    logger.info("ProcessCiscoAdvisoryEmails running.")
    try:
        folder_path = SiteSecrets.objects.filter(varname='ciscoadvisory_folder')[0].varvalue
    except Exception as e:
        logger.exception(f"ProcessCiscoAdvisoryEmails: No 'ciscoadvisory_folder' set in SiteSecrets.objects(): {e}")
        raise

    for filename in os.listdir(folder_path):
        path = os.path.join(folder_path, filename)
        if not (os.path.isfile(path) and filename.lower().endswith(('.eml', '.msg'))):
            continue
        try:
            with open(path, 'rb') as fp:
                html = read_html_from_message(fp)
            if not html:
                logger.warning("ProcessCiscoAdvisoryEmails: No HTML body found in %s; skipping.", filename)
                continue
            blocks = extract_advisory_blocks(html)
            if not blocks:
                logger.warning("ProcessCiscoAdvisoryEmails: No advisory tables found in %s.", filename)
                continue
            n = save_blocks(blocks)
            logger.info("ProcessCiscoAdvisoryEmails: %s: parsed %d blocks, created %d.", filename, len(blocks), n)
        except Exception as e:
            logger.exception("ProcessCiscoAdvisoryEmails: Failed processing %s: %s", filename, e)