#!/home/rc/api-monitoring/.venv/bin/python

from flask import Flask, jsonify
import psutil
import subprocess
import threading
import time
import socket
import platform

app = Flask(__name__)

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

def get_system_metrics():
    net_1 = psutil.net_io_counters()
    time.sleep(0.2)
    net_2 = psutil.net_io_counters()
    
    temp = 0.0
    try:
        temps = psutil.sensors_temperatures()
        if 'coretemp' in temps:
            temp = temps['coretemp'][0].current
        elif 'acpitz' in temps:
            temp = temps['acpitz'][0].current
    except: pass

    ram = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    
    return {
        "server_info": {
            "hostname": socket.gethostname(),
            "os": f"{platform.system()} {platform.release()}",
            "uptime_h": round((time.time() - psutil.boot_time()) / 3600, 1)
        },
        "cpu": {
            "usage_percent": psutil.cpu_percent(interval=None),
            "temp_c": temp,
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
        "storage": {
            "used_percent": disk.percent,
            "free_gb": round(disk.free / (1024**3), 2)
        }
    }

@app.route('/api/status', methods=['GET'])
def status_endpoint():
    return jsonify(get_system_metrics())

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)