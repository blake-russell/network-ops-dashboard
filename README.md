# Network Operations Dashboard #
---------------------------------
This project is a Network Operations Dashboard designed to centralize and streamline critical tasks for Network Operation Teams. It provides a single platform for automating workflows, managing confiugrations, and monitoring operational health across multiple network domains. The dashboard simplifies complex processess, improves visibility, and enhances security posture by integrating with key network infrastructure platforms.

## Key Features ##
### Automation & Configuration ###
    • Device Inventory
        ○ Create a source-of-truth repository of network devices, platforms, locations, credentials.
    • Cisco ACI Interface Configuration
        ○ Automates large-scale interface configurations.
    • F5 LTM Certificate Management
        ○ Simplifies SSL/TLS certificate renewals and profile updates.
    • ASA VPN Tools
        ○ Identifies VPN headend connections and enables user disconnect for security events.

### Operational Dashboard Insights ###
    • Real-time stats on VPN sessions, load distribution, and user counts.
    • Real-time Cisco SD-WAN vManage stats for low-performing sites
    • Proactive notifications for:
        ○ SSL/TLS certificate expiry
        ○ Service account password expiry
        ○ Circuit maintenance notifications
        ○ Cisco Advisory Field Notices

### On-Call Incident Management ###
    • Acts as a source-of-truth for in-flight incidents for on-call engineers.
    • Enables adding, updating, and closing incidents via a user-friendly interface.
    • Imports key alerts from other modules (circuit maintenance, expiring certificates, password expiration, etc).
    • Generates on-call summary reports for quick copy-and-paste updates to teams.
    • Automate reports to a team email distro and weekly shift changes.

### Circuit Maintenance Intelligence ###
    • Parses incoming vendor notifications. 
        ○ Supported Vendors:
        ○ Cogent
        ○ Windstream
    • Correlates impacted circuits with internal inventory.
    • Generates actionable reports to ensure planned maintenance awareness.

### Company Change Report ###
    • Parses Daily Company Change report into database.
        ○ Customize column_map to your own report

## Screenshots ##
### Dashboard ###
<img width="1262" height="797" alt="Image" src="https://github.com/user-attachments/assets/2daaf324-21d3-4d1d-94f4-a00821c908c9" />

### On-Call ###
<img width="1303" height="850" alt="Image" src="https://github.com/user-attachments/assets/2603118b-118e-46f6-88e7-e08f584111d9" />

### Inventory ###
<img width="1275" height="630" alt="Image" src="https://github.com/user-attachments/assets/166e783c-0640-47f0-a157-9accd2f6e609" />

### Circuits ###
<img width="1266" height="696" alt="Image" src="https://github.com/user-attachments/assets/7ab510af-2159-4e58-b6d6-1a9046526c3f" />

### Changes ###
<img width="1256" height="681" alt="Image" src="https://github.com/user-attachments/assets/c0294ca2-1996-4265-9302-68c92880e4fa" />

## Installation ##
### Prerequisites ###
    • Python 3.8+
    • Django 4.x
    • Linux subsystem w/ crontab access
    • Virtual environment tool (venv or pipenv)

### Setup ###
```
# Create virtual environment
python3 -m venv venv && cd venv/
source bin/activate  # macOS/Linux
Scripts\activate     # Windows

# Clone repository
git clone https://github.com/blake-russell/network-ops-dashboard.git
mv network-ops-dashboard/* .

# Create and modify secrets.py
mv src/network_ops_dashboard/secrets.py.example src/network_ops_dashboard/secrets.py

# Using something like MiniWebTool's django Secret Key Generator enter in a new SECRET_KEY
# Update the ALLOWED_HOSTS variable
# Modify the /pathto/ debug and request in logging
nano src/network_ops_dashboard/secrets.py

# Install dependencies
pip install -r requirements.txt

# Database migrations
python src/manage.py collectstatic
python src/manage.py migrate

# Create admin user
python manage.py createsuperuser

# Start development server
python manage.py runserver
```

## Configuration ##
    • Site Settings Configuration:
        ○ Company branding
        ○ Internal URLs
        ○ Sensitive credentials (via SiteSecrets)
    • Specific Module Configuration:
        ○ Look for customize or configure buttons on each module

## Usage ##
    1. Dashboard: View key operational metrics.
    2. On-Call Module:
        ○ Incident Management source-of-truth
        ○ Automatically generate summary reports to email distros
    3. Automation Tools:
        ○ Cisco ACI interface Configurations
        ○ F5 certificate renewal workflow
        ○ Cisco ASA VPN find and disco users
    4. Circuit Maintenance:
        ○ Parse vendor notices
        ○ Link to affected internal circuits
    5. Company Changes:
        ○ Parse internal change spreadsheet
        ○ Display changes for awareness
    6. Notifications:
        ○ SSL expiration
        ○ Service account password expiry
        ○ Cisco Field Notices

## Future Enhancements ##
    • Startup Script
    • Additional automation modules
    • Additional Dashboard metric cards

## Contributing ##
Pull requests are welcome! Please open an issue to discuss significant changes.

## License ##
MIT License – See [LICENSE](LICENSE.md) for details.