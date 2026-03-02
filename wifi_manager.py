import subprocess
import time

def get_wifi_list():
    try:
        subprocess.run(["nmcli", "device", "wifi", "rescan"], capture_output=True, text=True)
        time.sleep(1)
        
        cmd = ["nmcli", "-t", "-f", "SSID,SIGNAL,SECURITY,ACTIVE,BARS", "device", "wifi", "list"]
        result = subprocess.check_output(cmd, text=True, stderr=subprocess.DEVNULL)
        
        networks = []
        seen_ssids = set()
        
        for line in result.strip().split('\n'):
            if not line: continue
            parts = line.split(':')
            if len(parts) >= 4:
                ssid = parts[0]
                signal = parts[1]
                security = parts[2] if parts[2] else "Open"
                active = parts[3] == "yes"
                bars = parts[4] if len(parts) > 4 else ""

                if not ssid or ssid in seen_ssids or bars == "--":
                    continue
                
                networks.append({
                    "ssid": ssid,
                    "signal": signal,
                    "security": security,
                    "active": active
                })
                seen_ssids.add(ssid)
        
        return sorted(networks, key=lambda x: int(x['signal']), reverse=True)
    except Exception as e:
        return {"error": str(e)}

def connect_to_wifi(ssid, password):
    try:
        cmd = ["sudo", "nmcli", "device", "wifi", "connect", ssid, "password", password]
        process = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
        
        if process.returncode == 0:
            return {"status": "success", "message": f"Connected to {ssid}"}
        else:
            return {"status": "error", "message": process.stderr.strip()}
    except subprocess.TimeoutExpired:
        return {"status": "error", "message": "Connection timeout"}
    except Exception as e:
        return {"status": "error", "message": str(e)}