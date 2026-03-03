import subprocess
import json
from datetime import datetime

def get_ssh_logs():
    try:
        result = subprocess.run(
            ['sudo', 'journalctl', '-u', 'ssh', '-n', '1000', '--output=json', '--no-pager'],
            capture_output=True, text=True
        )
        
        successful_logins = []
        failed_logins = []
        
        for line in result.stdout.splitlines():
            if not line.strip(): continue
            try:
                entry = json.loads(line)
                message = entry.get("MESSAGE", "")
                
                ts = int(entry.get("__REALTIME_TIMESTAMP", 0)) / 1000000
                time_str = datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')

                if "Accepted" in message:
                    successful_logins.append({
                        "time": time_str,
                        "message": message,
                        "type": "success"
                    })
                elif "Failed password" in message or "Invalid user" in message:
                    failed_logins.append({
                        "time": time_str,
                        "message": message,
                        "type": "failed"
                    })
            except json.JSONDecodeError:
                continue
                
        who_result = subprocess.run(['who'], capture_output=True, text=True)
        active_users = []
        for line in who_result.stdout.splitlines():
            parts = line.split()
            if len(parts) >= 5:
                active_users.append({
                    "user": parts[0],
                    "terminal": parts[1],
                    "login_time": f"{parts[2]} {parts[3]}",
                    "ip": parts[4].strip("()")
                })
                
        return {
            "status": "success",
            "active_users_count": len(active_users),
            "active_users": active_users,
            "stats": {
                "total_success_logs": len(successful_logins),
                "total_failed_logs": len(failed_logins)
            },
            "history": {
                "success": successful_logins[-20:][::-1], 
                "failed": failed_logins[-20:][::-1]
            }
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}