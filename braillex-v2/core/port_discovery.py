import re
import json
import subprocess
import serial
import serial.tools.list_ports


def find_braillex_com_port():
    candidates = []

    # Method 1: pywin32 WMI
    try:
        import wmi

        c = wmi.WMI()
        for port in c.Win32_SerialPort():
            name = (port.Name or "").lower()
            desc = (port.Description or "").lower()
            caption = (port.Caption or "").lower()
            if "braillex" in name or "braillex" in desc or "braillex" in caption:
                m = re.search(r"(COM\d+)", port.Name or port.Caption or "")
                if m:
                    candidates.append((m.group(1), port.Name))
    except Exception:
        pass

    # Method 2: pyserial list_ports
    if not candidates:
        for p in serial.tools.list_ports.comports():
            combined = f"{p.description} {p.name} {p.manufacturer or ''} {p.hwid or ''}".lower()
            if "braillex" in combined or "hc-06" in combined or "bth" in combined:
                candidates.append((p.device, p.description))

    # Method 3: PowerShell registry scan
    if not candidates:
        try:
            ps_cmd = (
                "Get-PnpDevice -Class Ports | "
                "Where-Object { $_.FriendlyName -match 'braillex|hc-06' -or $_.InstanceId -match 'BTHENUM' } | "
                "Select-Object FriendlyName, InstanceId | ConvertTo-Json"
            )
            result = subprocess.run(
                ["powershell", "-NoProfile", "-Command", ps_cmd],
                capture_output=True,
                text=True,
                timeout=8,
            )
            if result.stdout.strip():
                data = json.loads(result.stdout)
                if isinstance(data, dict):
                    data = [data]
                for item in data:
                    name = item.get("FriendlyName", "")
                    m = re.search(r"(COM\d+)", name)
                    if m:
                        candidates.append((m.group(1), name))
        except Exception:
            pass

    # Method 4: broad Bluetooth COM scan
    if not candidates:
        try:
            ps_cmd = (
                "Get-PnpDevice -Class Ports | "
                "Where-Object { $_.InstanceId -match 'BTHENUM' } | "
                "Select-Object FriendlyName, InstanceId | ConvertTo-Json"
            )
            result = subprocess.run(
                ["powershell", "-NoProfile", "-Command", ps_cmd],
                capture_output=True,
                text=True,
                timeout=8,
            )
            if result.stdout.strip():
                data = json.loads(result.stdout)
                if isinstance(data, dict):
                    data = [data]
                for item in data:
                    name = item.get("FriendlyName", "")
                    m = re.search(r"(COM\d+)", name)
                    if m:
                        candidates.append((m.group(1), name))
        except Exception:
            pass

    if candidates:
        return candidates[0]
    return None, None


def get_all_com_ports():
    ports = []
    for p in serial.tools.list_ports.comports():
        ports.append((p.device, p.description))
    return ports
