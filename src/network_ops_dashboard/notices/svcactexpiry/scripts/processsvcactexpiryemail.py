import os
import base64
import logging
from datetime import datetime
from email import policy
from email.parser import BytesParser
from network_ops_dashboard.models import *
from network_ops_dashboard.notices.svcactexpiry.models import *

logger = logging.getLogger('network_ops_dashboard.svcactexpiry')

def clean_text(text):
    return ' '.join(text.replace('\xa0', ' ').split())

def decode_email(encoded_content):
    for part in encoded_content.walk():
        content_type = part.get_content_type()
        # content_disposition = part.get("Content-Disposition", "")
        content_transfer_encoding = part.get("Content-Transfer-Encoding", "").lower()
        # Look for text parts that are base64 encoded
        if content_type in ["text/plain", "text/html"] and content_transfer_encoding == "base64":
            payload = part.get_payload()  # this will still be base64 encoded
            decoded_bytes = base64.b64decode(payload)
            try:
                decoded_content = decoded_bytes.decode(part.get_content_charset() or 'utf-8', errors='replace')
                return decoded_content
            except Exception as e:
                logger.exception(f"ProcessSvcActExpiryEmails: Failed to decode email: {e}")
                raise

def ProcessSvcActExpiryEmails():
    logger.info(f"ProcessSvcActExpiryEmails Running.")
    try:
        folder_path = SiteSecrets.objects.filter(varname='svcactexpiry_folder')[0].varvalue
    except Exception as e:
        logger.exception(f"ProcessSvcActExpiryEmails: No 'svcactexpiry_folder' set in SiteSecrets.objects(): {e}")
        raise
    for filename in os.listdir(folder_path):
        file_path = os.path.join(folder_path, filename)
        if os.path.isfile(file_path) and filename.endswith('.msg'):
            try:
                with open(file_path, 'rb') as email:
                    logger.info(f"ProcessSvcActExpiryEmails: Processing SvcActExpiry Email {filename}.")
                    #split the email
                    encoded_content = BytesParser(policy=policy.default).parse(email)
                    decoded_content = decode_email(encoded_content)
                    
                    content0 = clean_text(decoded_content)
                    content1 = content0.split('Service account name, password reset due date')[1].strip()
                    content2 = content1.split('1. Password reset options:')[0].strip().replace(' ', ',')

                    parts = content2.split(',')
                    pairs = list(zip(parts[::2], parts[1::2]))

                    for username, date_str in pairs:
                        try:
                            expiry_date = datetime.strptime(date_str, "%m-%d-%Y").date()
                            obj, created = SvcActExpiry.objects.get_or_create(
                                svc_act = username,
                                expire_date = expiry_date
                            )
                            if created:
                                logger.info(f"ProcessSvcActExpiryEmails: SvcActExpiry object created: {username} - {expiry_date}")
                            else:
                                logger.info(f"ProcessSvcActExpiryEmails: SvcActExpiry object already exists: {username} - {expiry_date}")
                        except Exception as e:
                            logger.exception(f"ProcessSvcActExpiryEmails: SvcActExpiry object already exists for: {block['short_title']}. {e}")

            except Exception as e:
                logger.exception(f"ProcessSvcActExpiryEmails: Exception Processing SvcActExpiry Email {filename}. {e}")
                continue
        os.remove(file_path)
    return None