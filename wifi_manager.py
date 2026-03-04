import subprocess
import time

wifi_cache = {
    "data": [],
    "last_updated": 0
}
CACHE_TTL = 20

def get_wifi_list(force_rescan=False):
    global wifi_cache
    current_time = time.time()

    if not force_rescan and (current_time - wifi_cache["last_updated"] < CACHE_TTL):
        return wifi_cache["data"]

    try:
        if force_rescan:
            subprocess.run(["nmcli", "device", "wifi", "rescan"], timeout=5, capture_output=True)
        
        cmd = ["nmcli", "-t", "-e", "yes", "-f", "SSID,SIGNAL,SECURITY,ACTIVE,BARS", "device", "wifi", "list"]
        result = subprocess.check_output(cmd, text=True, stderr=subprocess.DEVNULL)
        
        networks = []
        seen_ssids = set()
        
        for line in result.strip().split('\n'):
            if not line: continue
            parts = line.replace('\\:', '___COLON___').split(':')
            
            if len(parts) >= 4:
                ssid = parts[0].replace('___COLON___', ':').strip()
                signal = parts[1].strip()
                security = parts[2].strip() if parts[2] else "Open"
                active = parts[3].strip() == "yes"
                bars = parts[4].strip() if len(parts) > 4 else ""

                if not ssid or ssid in seen_ssids or bars == "--":
                    continue
                
                networks.append({
                    "ssid": ssid,
                    "signal": int(signal) if signal.isdigit() else 0,
                    "security": security,
                    "active": active
                })
                seen_ssids.add(ssid)
        
        final_list = sorted(networks, key=lambda x: x['signal'], reverse=True)
        
        wifi_cache["data"] = final_list
        wifi_cache["last_updated"] = current_time
        
        return final_list
    except Exception as e:
        print(f"Error: {e}")
        return wifi_cache["data"]

def connect_to_wifi(ssid, password):
    try:
        cmd = ["sudo", "nmcli", "device", "wifi", "connect", ssid, "password", password]
        process = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
        
        if process.returncode == 0:
            return {"status": "success", "message": f"Connected to {ssid}"}
        else:
            return {"status": "error", "message": "Wrong password or signal lost"}
    except subprocess.TimeoutExpired:
        return {"status": "error", "message": "Connection timeout"}