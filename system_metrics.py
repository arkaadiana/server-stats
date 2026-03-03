import psutil
import subprocess
import threading
import time
import socket
import platform
import json

gpu_data = {
    "model": "Intel HD Graphics",
    "render_3d_percent": 0.0,
    "video_percent": 0.0,
    "power_w": 0.0,
    "status": "Initializing"
}

def monitor_intel_gpu():
    global gpu_data
    try:
        process = subprocess.Popen(
            ['sudo', 'intel_gpu_top', '-J'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        buffer = ""
        while True:
            line = process.stdout.readline()
            if not line and process.poll() is not None:
                break
                
            buffer += line
            
            try:
                if "}" in line and buffer.strip().startswith("{"):
                    clean_buffer = buffer.strip()
                    if clean_buffer.endswith(","):
                        clean_buffer = clean_buffer[:-1]
                        
                    data = json.loads(clean_buffer)
                    
                    if "engines" in data:
                        engines = data["engines"]
                        
                        if "Render/3D/0" in engines:
                            gpu_data["render_3d_percent"] = float(engines["Render/3D/0"].get("busy", 0.0))
                        if "Video/0" in engines:
                            gpu_data["video_percent"] = float(engines["Video/0"].get("busy", 0.0))
                            
                    if "power" in data and "GPU" in data["power"]:
                        gpu_data["power_w"] = float(data["power"]["GPU"].get("value", 0.0))
                        
                    gpu_data["status"] = "Active"
                    buffer = ""
                    
            except json.JSONDecodeError:
                continue
                
    except Exception as e:
        gpu_data["status"] = f"Error: {str(e)}"

threading.Thread(target=monitor_intel_gpu, daemon=True).start()

def get_cpu_temp():
    try:
        temps = psutil.sensors_temperatures()
        if not temps:
            return None
        
        for name in ['coretemp', 'acpitz', 'cpu_thermal']:
            if name in temps and len(temps[name]) > 0:
                return temps[name][0].current
                
        return list(temps.values())[0][0].current
    except Exception:
        return None

def get_all_storage():
    disk = []
    partitions = psutil.disk_partitions(all=False)
    for part in partitions:
        try:
            usage = psutil.disk_usage(part.mountpoint)
            disk.append({
                "device": part.device,
                "mountpoint": part.mountpoint,
                "filesystem": part.fstype,
                "total_gb": round(usage.total / (1024**3), 2),
                "used_gb": round(usage.used / (1024**3), 2),
                "used_percent": usage.percent
            })
        except: continue
    return disk

def get_full_metrics():
    net_1 = psutil.net_io_counters()
    time.sleep(0.2)
    net_2 = psutil.net_io_counters()
    ram = psutil.virtual_memory()
    
    return {
        "server_info": {
            "hostname": socket.gethostname(),
            "os": f"{platform.system()} {platform.release()}",
            "uptime_h": round((time.time() - psutil.boot_time()) / 3600, 1)
        },
        "cpu": {
            "usage_percent": psutil.cpu_percent(interval=None),
            "load_avg": psutil.getloadavg(),
            "temp_c": get_cpu_temp()
        },
        "ram": {
            "usage_percent": ram.percent,
            "used_gb": round(ram.used / (1024**3), 2),
            "total_gb": round(ram.total / (1024**3), 2)
        },
        "network": {
            "rx_kbps": round(((net_2.bytes_recv - net_1.bytes_recv) / 0.2) / 1024, 1),
            "tx_kbps": round(((net_2.bytes_sent - net_1.bytes_sent) / 0.2) / 1024, 1)
        },
        "intel_gpu": gpu_data,
        "storage": get_all_storage()
    }