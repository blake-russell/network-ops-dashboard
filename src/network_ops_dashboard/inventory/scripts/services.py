import napalm
from napalm.base.exceptions import ConnectionException
from django.utils import timezone

def pull_device_config(device):
    platform = (device.platform.name or "").lower() if device.platform else ""
    creds = device.creds_ssh

    driver_map = {
        "cisco": "ios",
        "nexus": "nxos",
        "crs": "iosxr",
        "juniper": "junos",
        "arista": "eos",
    }

    driver_name = next((drv for key, drv in driver_map.items() if key in platform), None)
    if not driver_name:
        raise ValueError(f"Unsupported platform for {device.name}: {platform}")

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
        driver_name2 = driver_name + "_ssh"
        driver2 = napalm.get_network_driver(driver_name2)
        conn = driver2(
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
