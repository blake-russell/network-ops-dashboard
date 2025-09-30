import ipaddress, subprocess
import paramiko
import re
import socket
import logging
import traceback
from django.shortcuts import get_object_or_404
from django.utils import timezone
from network_ops_dashboard.inventory.models import Inventory, NetworkCredential
from network_ops_dashboard.inventory.discovery.models import DiscoveryJob, DiscoveredDevice

logger = logging.getLogger('network_ops_dashboard.discovery')

def _snmp_get_sysdescr(ip, community="public", timeout=2):
    try:
        result = subprocess.run(
            ["snmpget", "-v2c", "-c", community, "-t", str(timeout), "-Ovq", ip, "1.3.6.1.2.1.1.1.0"],
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
            timeout=timeout+1
        )
        return result.stdout.strip() if result.returncode == 0 else None
    except Exception as e:
        logger.exception(f"_snmp_get_sysdescr - {e}")
        return None

def _snmp_get_sysname(ip, community="public", timeout=2):
    try:
        result = subprocess.run(
            ["snmpget", "-v2c", "-c", community, "-t", str(timeout), "-Ovq", ip, "1.3.6.1.2.1.1.5.0"],
            stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True, timeout=timeout+1
        )
        # 1.3.6.1.2.1.47.1.1.1.1.12.149 = entPhysicalMfgName (Cisco, Juniper, Arista)
        return result.stdout.strip().split('.')[0] if result.returncode == 0 else None
    except Exception as e:
        logger.exception(f"_snmp_get_sysname - {e}")
        return None

def _snmp_get_serialnumber(ip, community="public", timeout=2, oid="1.3.6.1.2.1.47.1.1.1.1.11.149"):
    try:
        result = subprocess.run(
            ["snmpget", "-v2c", "-c", community, "-t", str(timeout), "-Ovq", ip, oid],
            stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True, timeout=timeout+1
        )
        # Also try 11.1, 11.2 along with 11.149 for other vendors that might support one or the other.
        return result.stdout.strip().strip('"') if result.returncode == 0 else None
    except Exception as e:
        logger.exception(f"_snmp_get_serialnumber - {e}")
        return None
    
def _snmp_get_interfaces(ip, community="public", timeout=2):
    try:
        result = subprocess.run(
            ["snmpwalk", "-v2c", "-c", community, "-t", str(timeout), "-On", ip, "1.3.6.1.2.1.2.2.1.2"],
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
            timeout=timeout+3
        )
        '''
        .1.3.6.1.4.1.9 - OLD-CISCO-CHASSIS-MIB
        .1.3.6.1.4.1.2636 - JUNIPER-MIB
        .1.3.6.1.4.1.30065 - Arista
        .1.3.6.1.4.1.637 - Old ALU
        .1.3.6.1.4.1.12356 - FORTINET-MIB
        '''
        if result.returncode != 0:
            return []
        interfaces = []
        for line in result.stdout.splitlines():
            _, val = line.split(" = ", 1)
            interfaces.append(val.strip())
        return interfaces
    except Exception as e:
        logger.exception(f"_snmp_get_interfaces - {e}")
        return []
    
def _ip_list_from_subnet_or_range(block: str):
    block = (block or "").strip()
    ips = []
    if not block:
        return ips
    # allow multi-line input
    parts = []
    for line in block.splitlines():
        line = line.strip()
        if not line:
            continue
        if "," in line:
            parts.extend([p.strip() for p in line.split(",") if p.strip()])
        else:
            parts.append(line)
    for p in parts:
        if "-" in p:
            a,b = p.split("-",1)
            aip = ipaddress.ip_address(a.strip())
            bip = ipaddress.ip_address(b.strip())
            cur = int(aip)
            while cur <= int(bip):
                ips.append(str(ipaddress.ip_address(cur)))
                cur += 1
        elif "/" in p:
            net = ipaddress.ip_network(p, strict=False)
            for ip in net.hosts():
                ips.append(str(ip))
        else:
            ips.append(p)
    return ips

def _alive_ping(ip, timeout_s=1):
    try:
        # Linux: -c 1 (count) -W seconds (timeout)
        return subprocess.run(
            ["ping","-c","1","-W",str(timeout_s), ip],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        ).returncode == 0
    except Exception as e:
        logger.exception(f"_alive_ping - {e}")
        return False

def parse_sysdescr(sysdescr):
    vendor = "Unknown"
    pid = ""
    model = ""
    version = ""

    if "Cisco" in sysdescr:
        vendor = "Cisco"
        # Try for NX-OS/Nexus
        m = re.search(r'NX-OS\(tm\)\s+([^\s,]+)', sysdescr)
        if m:
            sn_oid = '1.3.6.1.2.1.47.1.1.1.1.11.149'
            pid = m.group(1).upper()
            model = f'Nexus {pid}'

        # Try for Catalyst
        m1 = re.search(r"(Catalyst)", sysdescr, re.IGNORECASE)
        if m1:
            sn_oid = '1.3.6.1.2.1.47.1.1.1.1.11.1'
            # Try for Catalyst 9K
            m11 = re.search(r"(CAT9K)", sysdescr, re.IGNORECASE)
            if m11:
                model = f'{m1.group(1)} {m11.group(1)}'
                pid = m11.group(1)

        # Try for IOS Version
        m = re.search(r'Version\s+([^\s,]+)', sysdescr)
        if m:
            version = m.group(1)

    return {
        "vendor": vendor,
        "platform": pid,
        "model": model,
        "version": version,
        "sn_oid": sn_oid,
    }

def parse_interfaces(raw_list):
    interfaces = []
    for entry in raw_list:
        # Remove leading "STRING: "
        if entry.startswith("STRING: "):
            interfaces.append(entry.split("STRING: ")[1].strip())
        else:
            interfaces.append(entry.strip())
    return interfaces

def reverse_dns(ip):
    try:
        return socket.gethostbyaddr(ip)[0].split('.')[0]
    except Exception as e:
        logger.exception(f"reverse_dns - {e}")
        return None
    
def ssh_exec(ip, username, password, cmd, timeout=5):
    try:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(ip, username=username, password=password, timeout=timeout, look_for_keys=False)
        stdin, stdout, stderr = client.exec_command(cmd)
        output = stdout.read().decode().strip()
        client.close()
        return output
    except Exception as e:
        logger.exception(f"ssh_exec - {e}")
        return None
    
def detect_platform(output):
    output = output.lower()
    if "nx-os" in output:
        return {"platform": "cisco_nxos", "vendor": "Cisco"}
    if "cisco ios software" in output:
        return {"platform": "cisco_ios", "vendor": "Cisco"}
    if "cisco adaptive security appliance" in output:
        return {"platform": "cisco_asa", "vendor": "Cisco"}
    if "arista" in output:
        return {"platform": "arista_eos", "vendor": "Arista"}
    if "junos" in output:
        return {"platform": "juniper_junos", "vendor": "Juniper"}
    if "huawei" in output:
        return {"platform": "huawei_vrp", "vendor": "Huawei"}
    if "vyos" in output:
        return {"platform": "vyos", "vendor": "VyOS"}
    return "unknown"

def run_platform_probe(ip, username, password, platform):
    if platform == "cisco_ios":
        ver = ssh_exec(ip, username, password, "show version")
        return {"show_version": ver}
    if platform == "cisco_nxos":
        inv = ssh_exec(ip, username, password, "show inventory")
        ver = ssh_exec(ip, username, password, "show version")
        intf = ssh_exec(ip, username, password, "show interface status")
        parse_inv = parse_nxos_inventory(inv)
        parse_ver = parse_nxos_version(ver)
        parse_intf = parse_nxos_interface_names(intf)
        return {"show_inventory": inv,
                "show_ver": ver,
                "show_int": intf,
                "model": parse_inv["model"], 
                "pid": parse_inv["pid"], 
                "serial": parse_inv["serial"],
                "version": parse_ver["version"],
                "hostname": parse_ver["hostname"],
                "interfaces": parse_intf
                }
    if platform == "juniper_junos":
        chs = ssh_exec(ip, username, password, "show chassis hardware")
        return {"chassis": chs}
    if platform == "arista_eos":
        ver = ssh_exec(ip, username, password, "show version")
        inv = ssh_exec(ip, username, password, "show inventory")
        return {"version": ver, "inventory": inv}
    return {}

def parse_nxos_inventory(inventory_output):
    chassis_info = {}

    # Split into inventory blocks (separated by blank lines)
    blocks = inventory_output.strip().split('\n\n')

    for block in blocks:
        if 'NAME: "Chassis"' in block:
            lines = block.splitlines()
            for l in lines:
                if "DESCR:" in l:
                    # Match embedded DESCR: field
                    m = re.search(r'DESCR:\s+"([^"]+)"', l)
                    if m:
                        model_raw = m.group(1)
                        # Remove "chassis" from end
                        chassis_info["model"] = re.sub(r'\s*chassis\s*$', '', model_raw, flags=re.IGNORECASE).strip()
                elif l.strip().startswith("PID:"):
                    # Extract PID and SN
                    m = re.search(r'PID:\s*([\w\-]+).*SN:\s*([\w\-]+)', l)
                    if m:
                        chassis_info["pid"] = m.group(1)
                        chassis_info["serial"] = m.group(2)
            break
    return chassis_info

def parse_nxos_version(output):
    version = ""
    hostname = ""
    lines = output.splitlines()
    for line in lines:
        line = line.strip()
        # Get hostname
        if line.lower().startswith("device name:"):
            hostname = line.split(":", 1)[-1].strip()
        # Get system version
        if line.lower().startswith("system:") and "version" in line.lower():
            m = re.search(r'version\s+([^\s,]+)', line, re.IGNORECASE)
            if m:
                version = m.group(1)
    return {"version": version, "hostname": hostname}

def parse_nxos_interface_names(output):
    interfaces = []
    lines = output.splitlines()
    started = False

    for line in lines:
        line = line.strip()
        if not line:
            continue
        # Skip headers
        if line.startswith("Port"):
            started = True
            continue
        if line.startswith("---") or not started:
            continue
        iface = line.split()[0]
        interfaces.append(iface)

    return interfaces


def run_discovery(job: DiscoveryJob):
    """
    Synchronous discovery. Reads job.params:
      - targets (multiline)
      - scan_kind ('icmp'/'snmp'/'ssh')
      - snmp_community (optional)
      - timeout (seconds)
    Creates DiscoveredDevice rows and updates job counters.
    """
    params = job.params or {}
    targets_str = params.get("targets", "")
    scan_kind   = params.get("scan_kind", "icmp")
    snmp_comm   = params.get("snmp_community") or ""
    credential = params.get("credential") or ""
    if credential:
        credobj = get_object_or_404(NetworkCredential, pk=credential)
        ssh_user   = credobj.username
        ssh_pass   = credobj.password
    timeout     = int(params.get("timeout") or 5)
    ips = _ip_list_from_subnet_or_range(targets_str)
    if not ips:
        job.completed = True
        job.result_count = 0
        job.result_summary = "No targets provided."
        job.save(update_fields=["completed","result_count","result_summary"])
        return 0, "No targets provided."
    existing = set(
        Inventory.objects.exclude(ipaddress_mgmt__isnull=True)
        .values_list("ipaddress_mgmt", flat=True)
    )
    total_count = len(ips)
    job.total_count = total_count
    job.save(update_fields=["total_count"])
    created_count = 0
    error_count = 0
    for ip in ips:
        try:
            if ip in existing:
                job.ignored_count += 1
                continue
            alive = _alive_ping(ip, timeout_s=timeout)
            discovered_via_ = "ping" if alive else "none"
            hostname = ""
            vendor = ""
            platform = ""
            model = ""
            serial = ""
            version = ""
            interfaces = []
            discovery_dump = {}
            raw = {"ping": alive}

            if scan_kind == "snmp" and alive and snmp_comm:
                sysdescr = _snmp_get_sysdescr(ip, snmp_comm, timeout)
                if sysdescr:
                    discovered_via_ = "snmp"
                    vendor_info = parse_sysdescr(sysdescr or "")
                    vendor = vendor_info.get("vendor", "")
                    model = vendor_info.get("model", "")
                    version = vendor_info.get("version", "")
                    serial = _snmp_get_serialnumber(ip, snmp_comm, timeout, vendor_info.get('sn_oid', ""))
                    platform = vendor_info.get("platform", "")
                    hostname = _snmp_get_sysname(ip, snmp_comm, timeout) or reverse_dns(ip)
                    interfaces_raw = _snmp_get_interfaces(ip, snmp_comm, timeout)
                    interfaces = parse_interfaces(interfaces_raw or [])
                    discovery_dump = sysdescr
                
            if scan_kind == "ssh" and alive:
                ssh_banner = ssh_exec(ip, ssh_user, ssh_pass, "show version")
                platform_guess = detect_platform(ssh_banner)
                platform_os = platform_guess.get("platform", "")
                vendor = platform_guess.get("vendor", "")
                components = run_platform_probe(ip, ssh_user, ssh_pass, platform_os)
                discovered_via_ = "ssh"
                hostname = components.get("hostname", "")
                model = components.get("model",  "")
                platform = components.get("pid",  "")
                serial = components.get("serial", "")
                version = components.get("version", "")
                interfaces = components.get("interfaces", "")
                discovery_dump = {
                    "show_inventory": components.get("show_inventory", ""),
                    "show_version": components.get("show_ver", "")
                    }

            DiscoveredDevice.objects.create(
                job=job,
                ip=ip,
                hostname=hostname,
                platform_guess=platform,
                discovered_via=discovered_via_,
                last_seen=timezone.now(),
                raw={
                    "discovery_dump": discovery_dump or "",
                    "interfaces": interfaces,
                    "hostname": hostname,
                    "vendor": vendor,
                    "model": model,
                    "pid": platform,
                    "version": version,
                    "serial": serial,
                }
            )
            created_count += 1
            job.processed_count += 1
            job.save(update_fields=["processed_count"])

        except Exception as e:
            # Exception but still save DiscoveredDevice
            DiscoveredDevice.objects.create(
                job=job,
                ip=ip,
                hostname=hostname,
                platform_guess=platform,
                discovered_via=discovered_via_,
                last_seen=timezone.now(),
                raw={
                    "discovery_dump": discovery_dump or "",
                    "interfaces": interfaces,
                    "hostname": hostname,
                    "vendor": vendor,
                    "model": model,
                    "pid": platform,
                    "version": version,
                    "serial": serial,
                    "error": str(e),
                    "traceback": traceback.format_exc(),
                },
            )
            error_count += 1
            job.processed_count += 1
            job.save(update_fields=["processed_count"])

    job.completed = True
    job.result_count = created_count
    job.error_count = error_count
    if error_count > 0:
        job.result_summary = f"Discovered {created_count} target(s); encountered {job.error_count} target error(s); ignored {job.ignored_count} already in Inventory."
    else:
        job.result_summary = f"Discovered {created_count} target(s); ignored {job.ignored_count} already in Inventory."
    job.save(update_fields=["completed","processed_count","error_count","ignored_count","result_count","result_summary"])
    return job.processed_count, job.result_count, job.error_count, job.ignored_count, job.result_summary