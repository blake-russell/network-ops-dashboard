import os
import re
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
import logging
from network_ops_dashboard.notices.certexpiry.models import *

logger = logging.getLogger('network_ops_dashboard.certexpiry')

def process_entrust(provider, folder_path):
    for filename in os.listdir(folder_path):
        file_path = os.path.join(folder_path, filename)
        if os.path.isfile(file_path) and filename.endswith('.msg'):
            try:
                with open(file_path, 'r', encoding = "ISO-8859-1") as email:
                    logger.info(f"ProcessCertExpiryEmails: Processing Entrust Email {filename}.")
                    #split the email
                    content0 = email.read()
                    content1 = content0.replace('=\n', '').replace('=3D', '=')
                    content2 = content1.split('The following certificates are set to expire in ')[-1]
                    #content2 = content1.split('\nSubject: Certificate Hub: ')[1] # Certificate Hub
                    content = content2.split('It is important to renew your certificates before they expire')[0].strip()
                    #content = content2.split('\nYou received this mandatory email announcement to update you about important changes to your certificate.')[0].strip() # Certificate Hub
                    # Parse relevant information
                    days = int(re.match(r'\d+', content).group()) if re.match(r'\d+', content) else 0
                    expire_date = datetime.today() + timedelta(days=days)
                    soup = BeautifulSoup(content, 'html.parser')
                    rows = soup.find_all('tr')
                    if len(rows) >= 2:
                        data_row = rows[1].find_all('td')
                        if len(data_row) >= 2:
                            cert_name = data_row[0].get_text(strip=True)
                            common_name = data_row[1].get_text(strip=True)
                        else:
                            logger.error(f"ProcessCertExpiryEmails: Not enough columns in data row: {filename}")
                    else:
                        logger.error(f"ProcessCertExpiryEmails: Not enough rows in table: {filename}")
                    if cert_name and common_name:
                        entry_qs = CertExpiry.objects.filter(cert_name=cert_name)
                        if entry_qs.exists():
                            logger.info(f"ProcessCertExpiryEmails: Entrust CertExpiry object exists already: {cert_name}")
                            pass
                        else:
                            CertExpiry.objects.create(provider=provider, cert_name=cert_name, common_name=common_name, expire_date=expire_date)
                            logger.info(f"ProcessCertExpiryEmails: Entrust CertExpiry object created: {cert_name}")
                    else:
                        logger.error(f"ProcessCertExpiryEmails: Unable to parse cert_name and common_name from: {filename}")
            except Exception as e:
                logger.exception('ProcessCertExpiryEmails: Exception Processing Entrust CertExpiry Email. {e}')
                continue
        os.remove(file_path)
    return None

def process_digicert(provider, folder_path):
    # Parse Digicert email
    logger.info(f"No function logic exists for Digicert (process_digicert) - Skipping.")
    return None

# Expand process handlers if needed