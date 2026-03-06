import json
import time
import subprocess
from datetime import datetime
from gpt4all import GPT4All

model = GPT4All("Llama-3.2-3B-Instruct-Q4_0.gguf", n_threads=4, device="cpu")

MAX_HISTORY_PUBLIC = 4
MAX_HISTORY_DASHBOARD = 10
SESSION_TIMEOUT = 3600

with open("prompt_public_chat.txt", "r", encoding="utf-8") as f:
    PROMPT_PUBLIC = f.read()

with open("prompt_dashboard.txt", "r", encoding="utf-8") as f:
    PROMPT_DASHBOARD = f.read()

COMMAND_MAP = {
    "REBOOT_SERVER": ["sudo", "/usr/sbin/reboot"],
    "SHUTDOWN_SERVER": ["sudo", "/usr/sbin/shutdown", "-h", "now"],
    "CANCEL_REBOOT": ["sudo", "/usr/sbin/shutdown", "-c"],
    "CLEAR_RAM": ["sudo", "/usr/local/bin/clear_ram.sh"]
}

active_sessions_public = {}
conversation_history_dashboard = []

def extract_json(reply_content):
    start_idx = reply_content.find('{')
    end_idx = reply_content.rfind('}') + 1
    if start_idx != -1 and end_idx != -1:
        return json.loads(reply_content[start_idx:end_idx])
    raise ValueError("Output bukan JSON")

def clean_old_sessions(current_time):
    expired = [sid for sid, data in active_sessions_public.items() if current_time - data['last_active'] > SESSION_TIMEOUT]
    for sid in expired:
        del active_sessions_public[sid]

def process_public_chat(user_message, session_id):
    current_time = time.time()
    clean_old_sessions(current_time)

    session_data = active_sessions_public.get(session_id)
    if session_data:
        if current_time - session_data['last_active'] < 5:
            return {"message": "Heeh! Jangan nyepam dong! Server kentang ini bisa meledak tahu!", "expression": "angry"}
    else:
        session_data = {'history': [], 'last_active': current_time}
        active_sessions_public[session_id] = session_data

    active_sessions_public[session_id]['last_active'] = current_time

    prompt = f"System: {PROMPT_PUBLIC}\n"
    for msg in session_data['history']:
        role_name = "Pengunjung" if msg['role'] == "user" else "Hersi"
        prompt += f"{role_name}: {msg['content']}\n"
    prompt += f"Pengunjung: {user_message}\nHersi:"

    try:
        response = model.generate(prompt, max_tokens=150, temp=0.3)
        parsed_json = extract_json(response.strip())

        session_data['history'].append({"role": "user", "content": user_message})
        session_data['history'].append({"role": "assistant", "content": json.dumps(parsed_json)})
        session_data['history'] = session_data['history'][-(MAX_HISTORY_PUBLIC * 2):]
        
        return parsed_json
    except Exception:
        return {"message": "Hmph! Tante lagi pusing mikir, CPU-nya lelah! Coba lagi nanti!", "expression": "baozhen"}

def get_datetime_context():
    now = datetime.now()
    hour = now.hour
    if 5 <= hour < 12: greeting = "pagi"
    elif 12 <= hour < 15: greeting = "siang"
    elif 15 <= hour < 18: greeting = "sore"
    else: greeting = "malam"

    return {
        "waktu_sekarang": now.strftime("%H:%M:%S"),
        "tanggal": now.strftime("%A, %d %B %Y"),
        "sesi": greeting
    }

def ask_hersiai(user_message, current_context):
    global conversation_history_dashboard

    datetime_ctx = get_datetime_context()
    full_context = {**datetime_ctx, **current_context}
    context_str = json.dumps(full_context, separators=(',', ':'))
    
    prompt = f"System: {PROMPT_DASHBOARD}\n\nData Server: {context_str}\n"
    for msg in conversation_history_dashboard:
        role_name = "Arka" if msg['role'] == "user" else "Hersi"
        prompt += f"{role_name}: {msg['content']}\n"
    prompt += f"Arka: {user_message}\nHersi:"

    try:
        response = model.generate(prompt, max_tokens=250, temp=0.3)
        parsed_json = extract_json(response.strip())

        conversation_history_dashboard.append({"role": "user", "content": user_message})
        conversation_history_dashboard.append({"role": "assistant", "content": json.dumps(parsed_json)})
        if len(conversation_history_dashboard) > (MAX_HISTORY_DASHBOARD * 2):
            conversation_history_dashboard = conversation_history_dashboard[-(MAX_HISTORY_DASHBOARD * 2):]

        return parsed_json
    except Exception:
        return {"action": "CHAT", "message": "Hmph! Tante lagi pusing mikirin kerjaan lain, Arka jangan ganggu dulu deh!", "delay_minutes": 0}

def process_hersi_request(user_message, current_context):
    hersi_decision = ask_hersiai(user_message, current_context)

    action = hersi_decision.get("action", "CHAT")
    message = hersi_decision.get("message", "Duh, ada yang salah nih.")
    delay = hersi_decision.get("delay_minutes", 0)

    if action == "CHAT":
        return {"status": "success", "reply": message}

    if action == "REBOOT_SERVER":
        try:
            if isinstance(delay, int) and delay > 0:
                cmd = ["sudo", "/usr/sbin/shutdown", "-r", f"+{delay}"]
            else:
                cmd = COMMAND_MAP["REBOOT_SERVER"]
            subprocess.Popen(cmd)
            return {"status": "success", "reply": message}
        except Exception as e:
            return {"status": "error", "reply": f"Hmph! Arka, servernya bandel nih nggak mau direboot: {str(e)}"}

    if action in COMMAND_MAP:
        try:
            subprocess.Popen(COMMAND_MAP[action])
            return {"status": "success", "reply": message}
        except Exception as e:
            return {"status": "error", "reply": f"Ngeselin banget sih, tante gagal jalanin perintahnya nih: {str(e)}"}

    return {"status": "error", "reply": "Hah? Maksud kamu apa, Arka? Tante nggak ngerti."}

def clear_history():
    global conversation_history_dashboard
    conversation_history_dashboard = []