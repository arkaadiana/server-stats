import subprocess
import re

def get_wifi_list():
    try:
        cmd = ["nmcli", "-t", "-f", "SSID,SIGNAL,SECURITY,ACTIVE", "device", "wifi", "list", "--rescan", "yes"]
        result = subprocess.check_output(cmd, text=True, stderr=subprocess.DEVNULL)
        
        networks = []
        seen_ssids = set()
        
        for line in result.strip().split('\n'):
            if not line: continue
            parts = line.split(':')
            if len(parts) >= 3:
                ssid = parts[0]
                if not ssid or ssid in seen_ssids: continue
                
                networks.append({
                    "ssid": ssid,
                    "signal": parts[1],
                    "security": parts[2] if parts[2] else "Open",
                    "active": parts[3] == "yes"
                })
                seen_ssids.add(ssid)
        return networks
    except Exception as e:
        return {"error": str(e)}

def connect_to_wifi(ssid, password):
    try:
        cmd = ["sudo", "nmcli", "device", "wifi", "connect", ssid, "password", password]
        process = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
        
        if process.returncode == 0:
            return {"status": "success", "message": f"Berhasil terhubung ke {ssid}"}
        else:
            return {"status": "error", "message": process.stderr.strip()}
            
    except subprocess.TimeoutExpired:
        return {"status": "error", "message": "Koneksi timeout. Cek password atau jarak router."}
    except Exception as e:
        return {"status": "error", "message": str(e)}