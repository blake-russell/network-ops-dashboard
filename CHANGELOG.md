# Changelog

## v0.3.1 - 10-20-2025
- 🆕 Inventory Config Backups: Added ability to fetch device configuration via NAPALM drivers.
- 🆕 Inventory Config Backups: Added ability automatically backup configurations on a daily/weekly basis.

## v0.3.0 - 10-10-2025
- 🖥️ Inventory: Re-design into single modal/page for CRUD process.
- 🆕 Inventory Tracked Interface: Added ability to add interfaces in order to "track" for particular scripts and cards such as Statseeker

## v0.2.9 - 10-3-2025
- 🆕 Inventory Discovery: Added SNMP/SSH device discovery functionality.
- 🗃️ DiscoveryJob Tasks: Added capability for job queuing discovery tasks.

## v0.2.8 - 09-26-2025
- 🆕 CiscoAdvisory: Added user assignment and status workflow.
- ✅ On-call: Fix parsehandler bugs for Cogent email processing.
- ✅ ASAVPN: Fixed unreachable stats.

## v0.2.7 - 09-03-2025
- 🆕 CiscoAdvisory: Added functionality to interact with field notices to maintain impact and remediation.
- ⚙️ CiscoAdvisory: Field Notices set as "No Impact" will auto-archive at specified On-Call auto-archive timeframe.
- 🗃️ Redis: Added Redis support/requirement for cache gated polling events.

## v0.2.6 - 08-29-2025
- 🆕 Dashboard: Added Statseeker Alarming Card Integration.
- ✅ CiscoAdvisory: Fixed bug in collector scripts.

## v0.2.5 - 08-25-2025
- 🆕 Dashboard: Added PagerDuty Incident Card Integration.

## v0.2.4 - 08-22-2025
- 🆕 Dashboard: Added ASAVPN Stats Configuration.
- 🖥️ On-call: Enable modification of incident titles.

## v0.2.3 - 08-21-2025
- 🆕 Dashboard: Added SD-WAN/vManage Statistics Card.
- ⚙️ Dashboard: Dynamic card data refreshes automatically.
- 🖥️ Dashboard/UX: Compacted configuration modal settings for dashboard cards.

## v0.2.2 - 08-15-2025
- ⚙️ On-call: Added ability to auto-archive incidents that are "Closed" daily or weekly at a provided time.
- ✅ On-call: Added status "Archived". Incident log will now show incidents that are "Archived".
- ✅ Scripts: Lookup NetworkCredential from Inventoy object instead of referring to it due to duplicates and ease.
- 🗃️ Inventory.object: Add Forgeignkey fields to NetworkCredential for SSH and REST.
- 🖥️ UX: Added superuser views to edit/add SiteSettings & SiteSettingsWebsites.
- 🖥️ UX: Added staff views to edit/add SiteSecrets to function with network scripts.
- 🖥️ UX: Added net-admin views to edit/add NetworkCredential & added new model field "username_search_field"

## v0.2.1 - 08-15-2025
- 🖥️ UX: Added styling to all buttons across the project.
- ⚙️ Filters: Added filtering to Iventory, Sites, Reports/Changes, Reports/Circuits, & Reports/Circuits/Circuit
- 🆕 On-call: Added email settings, automated cronjob enablement, & module configuration modal.

## v0.2.0 - 08-14-2025
- 🆕 Dashboard: Added customize button to arrange & toggle display of cards. Staff users can also enable/disable scripted cards & change script settings.
- 🆕 Reports & Notices: All email based reports/notice pages have been given an email processing to allow staff users ability to enable/disable & set time.
- 🤖 Cronjobs: No more static configuration of cronjobs, that is now all handled through the UI. Jobs utilize management/command calls to manage.py.
- ⚙️ Added soft warning for site-admin and staff users to warn when non staff/admin users don't have any assigned groups.
- ⚙️ Added DashboardPrefs model to track user-specific dashboard layout.
- ⚙️ Added FeatureFlags model to track enablement of dashboard card scripts and cronjobs.
- ⚙️ Added CompanyChangesSettings model to manage CompanyChanges modules settings from module page.

## v0.1.7 - 08-12-2025
- 🆕 Dashboard: Add CHANGELOG.md and deliver content to "Recent Changes" card on dashboard.
- ⚙️ Removed SiteChanges model.

## v0.1.6 - 08-08-2025
- 🆕 Reports/Circuit: Added cogent processhandler to process cogent maintenance report emails.
- 🚀 Reports/Circuit: Created module tests for pytest workflow.
- 🚀 Workflow: Cleaned Reports/Circuit module for flake8 testing.
- ⚙️ Config: Replaced deprecated "url" command with "re_path" in all urls.py to appease pytest.

## v0.1.5 - 08-06-2025
- 🚀 Workflow: Created workflow in GitActions for CI.
- 🚀 Workflow: Added docker build to test build and run pytests and linting.
- 🚀 Workflow: Run flake8 for linting.
- 🚀 Workflow: Added manage.py and create dummy secrets.py in workflow for testing.
- 🚀 ASAVPN: Added module tests for pytests in workflow.

## v0.1.4 - 07-31-2025
- 🛠️ On-call: Small improvements show incident owner, who closed incident in log.
- 🆕 Added Reports/Changes module to track company changes via xlsx intake.
- 🆕 Added Notices/Cisco Advisory module to intake Field Notices from Cisco to track and manage closure.
- 🆕 Added Notices/Certificate Expiry module to intake certificate expiry notices to track and manage closure.
- 🆕 Added Notices/Service Account Expiry module to intake service account password expiry notices to track and manage closure.
- 📈 Dashboard: show latest notices and site updates.

## v0.1.3 - 07-17-2025
- 🆕 Added Oncall module: SoT for on-call incidents and reporting
- ⚙️ Removed sensitive information and developed an open-source repo of the project

## v0.1.2 - 07-15-2025
- 🛠️ Reports/Circuit: Processhandler for Windstream hardened and process improvements
- 🛠️ ASAVPN: Shape input into script if necessary. Added log filter.
- 🤖 F5LB: Added AJAX scripting to templates to allow user to pull configuration from device into MOP objects dynamically.
- 🤖 APIC: Added AJAX scripting to templates to allow user to pull configuuration from device into MOP objects dynamically.
- 🛠️ APIC: Hardened the MOP process to prevent conflicts if APIC device was changed before deployment.

## v0.1.1 - 07-11-2025 - Initial Build
- 🆕 ASAVPN: Find & Disco User
- 🆕 ASAVPN: VPN User stats card
- 🆕 Reports/Circuit Maintenance Reports
- 🆕 APIC: Mass Interface Configuration
- 🆕 F5LB: Update VIP Certificate
- 🆕 Inventory: Device, Location, Platform database