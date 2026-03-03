import psutil
import subprocess
import threading
import time
import socket
import platform
import json
import os

gpu_data = {
    "model": "Intel Integrated Graphics",
    "render_3d_percent": 0.0,
    "video_percent": 0.0,
    "power_w": 0.0,
    "status": "Initializing"
}

def monitor_intel_gpu():
    global gpu_data
    subprocess.run(['sudo', 'killall', '-9', 'intel_gpu_top'], capture_output=True)
    time.sleep(1)
    
    while True:
        proc = None
        try:
            proc = subprocess.Popen(
                ['sudo', 'intel_gpu_top', '-J'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1
            )
            
            buffer = ""
            brace_count = 0
            start_idx = None
            
            for line in proc.stdout:
                buffer += line
                for i, ch in enumerate(line):
                    abs_i = len(buffer) - len(line) + i
                    if ch == '{':
                        if brace_count == 0:
                            start_idx = len(buffer) - len(line) + i
                        brace_count += 1
                    elif ch == '}':
                        brace_count -= 1
                        if brace_count == 0 and start_idx is not None:
                            json_str = buffer[start_idx:len(buffer) - len(line) + i + 1]
                            try:
                                data = json.loads(json_str)
                                engines = data.get("engines", {})
                                gpu_data["render_3d_percent"] = round(float(engines.get("Render/3D", {}).get("busy", 0)), 1)
                                gpu_data["video_percent"] = round(float(engines.get("Video", {}).get("busy", 0)), 1)
                                gpu_data["power_w"] = round(float(data.get("power", {}).get("GPU", 0)), 1)
                                gpu_data["status"] = "Active"
                            except:
                                pass
                            buffer = ""
                            start_idx = None
                            
        except Exception as e:
            gpu_data["status"] = f"Error: {str(e)}"
        finally:
            if proc:
                try:
                    proc.kill()
                    proc.communicate()
                except:
                    pass
            subprocess.run(['sudo', 'killall', '-9', 'intel_gpu_top'], capture_output=True)
            
        time.sleep(2)

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
        except:
            continue
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
            "usage_percent": psutil.cpu_percent(interval=1.0),
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

def log_for_pm2():
    while True:
        try:
            metrics = get_full_metrics()
            gpu = metrics["intel_gpu"]
            log_line = (
                f"[MONITOR] "
                f"CPU: {metrics['cpu']['usage_percent']}% | "
                f"RAM: {metrics['ram']['usage_percent']}% | "
                f"GPU: {gpu['render_3d_percent']}% | "
                f"Video: {gpu['video_percent']}% | "
                f"Power: {gpu['power_w']}W | "
                f"GPU Status: {gpu['status']}"
            )
            print(log_line, flush=True)
        except Exception as e:
            print(f"[MONITOR ERROR] {str(e)}", flush=True)
        time.sleep(5)

threading.Thread(target=monitor_intel_gpu, daemon=True).start()
threading.Thread(target=log_for_pm2, daemon=True).start()

if __name__ == "__main__":
    print("Server Monitoring Service Started", flush=True)
    while True:
        time.sleep(60)