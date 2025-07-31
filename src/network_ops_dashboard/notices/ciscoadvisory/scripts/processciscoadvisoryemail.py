import os
import base64
import logging
from datetime import datetime
from email import policy
from email.parser import BytesParser
from bs4 import BeautifulSoup
from network_ops_dashboard.models import *
from network_ops_dashboard.notices.ciscoadvisory.models import *

logger = logging.getLogger('network_ops_dashboard.ciscoadvisory')

def decode_email(encoded_content):
    for part in encoded_content.walk():
        content_type = part.get_content_type()
        content_disposition = part.get("Content-Disposition", "")
        content_transfer_encoding = part.get("Content-Transfer-Encoding", "").lower()
        # Look for text parts that are base64 encoded
        if content_type in ["text/plain", "text/html"] and content_transfer_encoding == "base64":
            payload = part.get_payload()  # this will still be base64 encoded
            decoded_bytes = base64.b64decode(payload)
            try:
                decoded_content = decoded_bytes.decode(part.get_content_charset() or 'utf-8', errors='replace')
                return decoded_content
            except Exception as e:
                logger.exception(f"ProcessCiscoAdvisoryEmails: Failed to decode email: {e}")
                raise

def clean_text(text):
    return ' '.join(text.replace('\xa0', ' ').split())

def ProcessCiscoAdvisoryEmails():
    logger.info(f"ProcessCiscoAdvisoryEmails Running.")
    try:
        folder_path = SiteSecrets.objects.filter(varname='ciscoadvisory_folder')[0].varvalue
    except Exception as e:
        logger.exception(f"ProcessCiscoAdvisoryEmails: No 'ciscoadvisory_folder' set in SiteSecrets.objects(): {e}")
        raise
    for filename in os.listdir(folder_path):
        file_path = os.path.join(folder_path, filename)
        if os.path.isfile(file_path) and filename.endswith('.msg'):
            try:
                with open(file_path, 'rb') as email:
                    logger.info(f"ProcessCiscoAdvisoryEmails: Processing CiscoAdvisory Email {filename}.")
                    #split the email
                    encoded_content = BytesParser(policy=policy.default).parse(email)

                    for part in encoded_content.walk():
                        content_type = part.get_content_type()
                        content_disposition = part.get("Content-Disposition", "")
                        content_transfer_encoding = part.get("Content-Transfer-Encoding", "").lower()
                        # Look for text parts that are base64 encoded
                        if content_type in ["text/plain", "text/html"] and content_transfer_encoding == "base64":
                            payload = part.get_payload()  # this will still be base64 encoded
                            decoded_bytes = base64.b64decode(payload)
                            try:
                                decoded_content = decoded_bytes.decode(part.get_content_charset() or 'utf-8', errors='replace')
                            except Exception as e:
                                logger.exception(f"ProcessCiscoAdvisoryEmails: Failed to decode email {filename}: {e}")
                                raise
                    
                    #soup = BeautifulSoup(decode_email(encoded_content), 'html.parser')
                    soup = BeautifulSoup(decoded_content, 'html.parser')
                    data_blocks = []

                    for h3 in soup.find_all('h3'):
                        content = {}
                        content['short_title'] = h3.get_text(strip=True).replace('\xa0', ' ')
                        table = h3.find_next("table")
                        rows = table.find_all("tr")

                        for row in rows:
                            cells = row.find_all("td")
                            if len(cells) < 2:
                                continue

                            label = clean_text(cells[0].get_text())
                            value_td = cells[1]

                            if "Title:" in label:
                                link = value_td.find("a")
                                content["long_title"] = clean_text(link.get_text()) if link else clean_text(value_td.get_text())
                                content["long_title_url"] = link['href'] if link and link.has_attr('href') else None
                            elif "Impact Rating:" in label:
                                content["impact_rating"] = value_td.get_text(strip=True).replace('\xa0', ' ')
                            elif "Description:" in label:
                                full_text = ' '.join(value_td.stripped_strings)
                                content["description"] = clean_text(full_text)
                            elif "Date:" in label:
                                date_str = clean_text(value_td.get_text())
                                try:
                                    content["date"] = datetime.strptime(date_str, "%d-%b-%Y").date()
                                except ValueError:
                                    content["date"] = datetime.today()

                        data_blocks.append(content)

                    for block in data_blocks:
                        exists = CiscoAdvisory.objects.filter(
                            title_short = block["short_title"],
                            date = block["date"]
                        ).exists()
                        try:
                            if not exists:
                                CiscoAdvisory.objects.create(
                                    title_short = block["short_title"],
                                    title = block.get("long_title"),
                                    url = block.get("long_title_url"),
                                    impact_rating = block.get("impact_rating"),
                                    description = block.get("description"),
                                    date = block["date"]
                                )
                                logger.info(f"ProcessCiscoAdvisoryEmails: CiscoAdvisory object created: {block['short_title']}")
                            else:
                                logger.info(f"ProcessCiscoAdvisoryEmails: CiscoAdvisory object already exists: {block['short_title']}")
                        except Exception as e:
                            logger.exception(f"ProcessCiscoAdvisoryEmails: CiscoAdvisory object already exists for: {block['short_title']}. {e}")

            except Exception as e:
                logger.exception(f"ProcessCiscoAdvisoryEmails: Exception Processing CiscoAdvisory Email {filename}. {e}")
                continue
        os.remove(file_path)
    return None