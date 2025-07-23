# Network Operations Dashboard #
---------------------------------
This project is a Network Operations Dashboard designed to centralize and streamline critical tasks for IT Network teams. It provides a single platform for automating workflows, managing confiugrations, and monitoring operational health across multiple network domains. The dashboard simplifies complex processess, improves visibility, and enhances security posture by integrating with key network infrastructure platforms.

## Key Features ##
### Automation & Configuration ###
    • Cisco ACI Interface Turn-Up
        ○ Automates large-scale interface configurations.
    • F5 LTM Certificate Management
        ○ Simplifies SSL/TLS certificate renewals and profile updates.
    • ASA VPN Tools
        ○ Identifies VPN headend connections and enables user disconnect for security events.

### On-Call Incident Management ###
    • Acts as a living source of in-flight incidents for on-call engineers.
    • Enables adding, updating, and closing incidents via a user-friendly interface.
    • Imports key alerts from other modules (circuit maintenance, expiring certificates, password expiration).
    • Generates on-call summary reports for quick copy-and-paste updates to teams.

### Operational Insights ###
    • Real-time stats on VPN sessions, load distribution, and user counts.
    • Proactive notifications for:
        ○ SSL/TLS certificate expiry
        ○ Service account password expiry
        ○ Circuit maintenance notifications (parsed from vendor emails)


### Circuit Maintenance Intelligence ###
    • Parses incoming vendor notifications.
    • Correlates impacted circuits with internal inventory.
    • Generates actionable reports to ensure planned maintenance awareness.


### Extensible Framework ###
    • Modular architecture for adding new tools and features.
    • Designed for scaling with additional dashboards and API integrations.

## Architecture Diagram ##
```
graph TD
    A[User Interface (Django Templates)] --> B[Django Views & Forms]
    B --> C[Business Logic (Python Automation Scripts)]
    C --> D[Database (PostgreSQL / SQLite)]
    C -->|REST API Calls| E[Cisco ACI / F5 LTM / ASA VPN]
    B --> F[Email Parser for Circuit Maintenance]
    D --> G[SiteSecrets / SiteSettings (Configuration Management)]
```

## Screenshots ##
Coming Soon

## Installation ##
### Prerequisites ###
    • Python 3.8+
    • Django 4.x
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
# Also update the ALLOWED_HOSTS variable
# And modify the /pathto/ debug and request logging on lines 23 & 31
nano src/network_ops_dashboard/secrets.py

# Install dependencies
pip install -r requirements.txt

# Database migrations
python src/manage.py migrate

# Create admin user
python manage.py createsuperuser

# Start development server
python manage.py runserver
```

## Configuration ##
    • Use Django Admin to set:
        ○ Company branding
        ○ Internal URLs
        ○ Sensitive credentials (via SiteSecrets)
    • Configure email parser settings for maintenance notifications.
    • Define alert thresholds for SSL and password expiry.

## Usage ##
    1. Dashboard: View key operational metrics.
    2. On-Call Module:
        ○ Manage in-flight incidents
        ○ Generate summary report for email updates
    3. Automation Tools:
        ○ Cisco ACI interface turn-up
        ○ F5 certificate renewal workflow
    4. Circuit Maintenance:
        ○ Parse vendor notices
        ○ Link to affected internal circuits
    5. Notifications:
        ○ SSL expiration
        ○ Service account password expiry

## Future Enhancements ##
    • RBAC (Role-Based Access Control)
    • WebSocket-powered live updates
    • API endpoints for integration
    • Enhanced reporting (PDF, Excel export)
    • Additional automation modules

## Contributing ##
Pull requests are welcome! Please open an issue to discuss significant changes.

## License ##
MIT License – See [LICENSE](LICENSE.md) for details.