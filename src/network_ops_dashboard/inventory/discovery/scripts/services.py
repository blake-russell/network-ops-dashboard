import ipaddress, subprocess
import paramiko
import re
import socket
from django.utils import timezone
from network_ops_dashboard.inventory.models import Inventory
from network_ops_dashboard.inventory.discovery.models import DiscoveryJob, DiscoveredDevice

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
    except Exception:
        return None

def _snmp_get_sysname(ip, community="public", timeout=2):
    try:
        result = subprocess.run(
            ["snmpget", "-v2c", "-c", community, "-t", str(timeout), "-Ovq", ip, "1.3.6.1.2.1.1.5.0"],
            stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True, timeout=timeout+1
        )
        # 1.3.6.1.2.1.47.1.1.1.1.12.149 = entPhysicalMfgName (Cisco, Juniper, Arista)
        return result.stdout.strip().split('.')[0] if result.returncode == 0 else None
    except Exception:
        return None

def _snmp_get_serialnumber(ip, community="public", timeout=2, oid="1.3.6.1.2.1.47.1.1.1.1.11.149"):
    try:
        result = subprocess.run(
            ["snmpget", "-v2c", "-c", community, "-t", str(timeout), "-Ovq", ip, oid],
            stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True, timeout=timeout+1
        )
        # Also try 11.1, 11.2 along with 11.149 for other vendors that might support one or the other.
        return result.stdout.strip().strip('"') if result.returncode == 0 else None
    except Exception:
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
    except Exception:
        return []
    
def _ssh_probe(ip, username, password, timeout=5):
    try:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(ip, username=username, password=password, timeout=timeout)
        stdin, stdout, stderr = client.exec_command("show version")
        version_output = stdout.read().decode()
        stdin, stdout, stderr = client.exec_command("show hostname")
        hostname = stdout.read().decode().strip()
        client.close()
        return {
            "hostname": hostname,
            "version_output": version_output,
        }
    except Exception as e:
        return None
    
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
    except Exception:
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
    except Exception:
        return None

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
    created_count = 0
    for ip in ips:
        if ip in existing:
            job.ignored_count += 1
            continue
        alive = _alive_ping(ip, timeout_s=timeout)
        discovered_via = "ping" if alive else "none"
        hostname = ""
        platform_guess = ""
        serial = ""
        interfaces = []
        raw = {"ping": alive}

        if scan_kind == "snmp" and alive and snmp_comm:
            sysdescr = _snmp_get_sysdescr(ip, snmp_comm, timeout)
            if sysdescr:
                discovered_via = "snmp"
                vendor_info = parse_sysdescr(sysdescr or "")
                serial = _snmp_get_serialnumber(ip, snmp_comm, timeout, vendor_info['sn_oid'])
                hostname = _snmp_get_sysname(ip, snmp_comm, timeout) or reverse_dns(ip)
                interfaces_raw = _snmp_get_interfaces(ip, snmp_comm, timeout)
                interfaces = parse_interfaces(interfaces_raw or [])
                raw["sysdescr"] = sysdescr
                raw["interfaces"] = interfaces_raw
                raw["hostname"] = hostname
                raw["serial"] = serial
                

        if scan_kind == "ssh" and alive:
            creds = job.get_credential_object()
            result = _ssh_probe(ip, creds.username, creds.password)
            if result:
                hostname = result["hostname"]
                platform_guess = result["version_output"]
                discovered_via = "ssh"
                raw["ssh_version"] = result["version_output"]

        DiscoveredDevice.objects.create(
            job=job,
            ip=ip,
            hostname=hostname,
            platform_guess=vendor_info["platform"],
            discovered_via=discovered_via,
            last_seen=timezone.now(),
            raw={
                "ping": alive,
                "sysdescr": sysdescr,
                "interfaces": interfaces,
                "hostname": hostname,
                "vendor": vendor_info["vendor"],
                "model": vendor_info["model"],
                "pid": vendor_info["platform"],
                "version": vendor_info["version"],
                "serial": serial,
            }
        )
        created_count += 1
        job.processed_count += 1

    job.completed = True
    job.result_count = created_count
    job.result_summary = f"Discovered {created_count} target(s); ignored {job.ignored_count} already in Inventory."
    job.save(update_fields=["completed","processed_count","ignored_count","result_count","result_summary"])
    return created_count, job.result_summary