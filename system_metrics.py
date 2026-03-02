import psutil
import subprocess
import threading
import time
import socket
import platform

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
            ['sudo', 'intel_gpu_top', '-l'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        for line in iter(process.stdout.readline, ''):
            line = line.strip()
            if "Render/3D" in line:
                parts = line.split()
                if len(parts) > 1:
                    gpu_data["render_3d_percent"] = float(parts[1].replace('%', ''))
            elif "Video" in line and "VideoEnhance" not in line:
                parts = line.split()
                if len(parts) > 1:
                    gpu_data["video_percent"] = float(parts[1].replace('%', ''))
            elif " W;" in line:
                try:
                    gpu_data["power_w"] = float(line.split(" W;")[0].split()[-1])
                except: pass
            gpu_data["status"] = "Active"
    except Exception as e:
        gpu_data["status"] = f"Error: {str(e)}"
        
threading.Thread(target=monitor_intel_gpu, daemon=True).start()

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
            "load_avg": psutil.getloadavg()
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