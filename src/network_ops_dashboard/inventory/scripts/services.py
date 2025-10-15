import napalm
from napalm.base.exceptions import ConnectionException
from django.utils import timezone
import re
import logging

logger = logging.getLogger('network_ops_dashboard.inventory.fetch-config')

def detect_napalm_driver(manufacturer: str, platform: str, device_name: str = ""):
    man = (manufacturer or "").lower().strip()
    plat = (platform or "").lower().strip()

    # explicit platform-based patterns
    platform_map = {
        r"nexus|n7k|n9k|nxos": "nxos",
        r"ios[-_ ]?xr|asr9k|crs": "iosxr",
        r"ios[-_ ]?xe|cat9k|cat8k|asr1k": "ios",   # XE handled by ios driver
        r"asa|firepower": "asa",
        r"panos|palo[-_ ]alto": "panos",
        r"eos|arista": "eos",
        r"junos|mx|ex|qfx": "junos",
        # r"forti|fortigate": "fortios", # pip install git+https://github.com/napalm-automation-community/napalm-fortios.git@master
        # r"aruba|hp": "aruba", # pip install git+https://github.com/napalm-automation-community/napalm-aruba.git
    }

    for pattern, driver in platform_map.items():
        if re.search(pattern, plat):
            return driver
        
    # fallback to manufacturer-based patterns
    manufacturer_map = {
        r"cisco": "ios",
        r"juniper": "junos",
        r"arista": "eos",
        r"palo": "panos",
        # r"fortinet": "fortios", # pip install git+https://github.com/napalm-automation-community/napalm-fortios.git@master
        # r"aruba|hp": "aruba", # pip install git+https://github.com/napalm-automation-community/napalm-aruba.git
    }
    for pattern, driver in manufacturer_map.items():
        if re.search(pattern, man):
            return driver
        
    # fallback or raise
    raise ValueError(f"Unsupported platform for {device_name}: {manufacturer} / {platform}")


def pull_device_config(device):
    platform = (device.platform.name or "").lower() if device.platform else ""
    manufacturer = (device.platform.manufacturer or "").lower() if device.platform else ""
    creds = device.creds_ssh

    try:
        driver_name = detect_napalm_driver(manufacturer, platform, device.name)
        logger.debug(f"fetch-config: Using NAPALM driver '{driver_name}' for {device.name}")
    except ValueError as e:
        logger.error(str(e))

    driver = napalm.get_network_driver(driver_name)

    conn = driver(
        hostname=str(device.ipaddress_mgmt),
        username=creds.username,
        password=creds.password,
        optional_args={"timeout": 20},
    )

    try:
        conn.open()
    except ConnectionException as e:
        # Fallback to IOS if restapi not configured
        if "503" in str(e) or "Connection refused" in str(e):
            driver503 = napalm.get_network_driver("ios")
            conn = driver503(
            hostname=str(device.ipaddress_mgmt),
            username=creds.username,
            password=creds.password,
            optional_args={"transport": "ssh",
                           "secret": creds.password,
                           "global_delay_factor": 2,
                           "auto_enable": True,
                           "timeout": 20},
            )
            conn.open()
            # ASA Term Pager
            try:
                conn.device.send_command("terminal pager 0")
            except Exception as e:
                logger.warning(f"{device.name}: Failed to disable ASA pager: {e}")
        # Otherwise fallback to ssh driver
        else:
            driver_name_ssh = driver_name + "_ssh"
            driver_ssh = napalm.get_network_driver(driver_name_ssh)
            conn = driver_ssh(
                hostname=str(device.ipaddress_mgmt),
                username=creds.username,
                password=creds.password,
                optional_args={"timeout": 20},
            )
            conn.open()
    configs = conn.get_config()
    conn.close()

    device.config_running = configs.get("running", "")
    device.config_startup = configs.get("startup", "")
    device.last_config_pull = timezone.now()
    device.save(update_fields=["config_running", "config_startup", "last_config_pull"])

    return device
