import os
import json
import time
import subprocess
from datetime import datetime
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(
    api_key=os.getenv("GROQ_API_KEY"),
    base_url="https://api.groq.com/openai/v1",
)

GROQ_MODEL = "llama-3.3-70b-versatile"

MAX_HISTORY_PUBLIC = 6
MAX_TOKENS_PUBLIC = 150
SESSION_TIMEOUT_PUBLIC = 3600

MAX_HISTORY_DASHBOARD = 20

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

def clean_old_sessions(current_time):
    expired = [sid for sid, data in active_sessions_public.items() if current_time - data['last_active'] > SESSION_TIMEOUT_PUBLIC]
    for sid in expired:
        del active_sessions_public[sid]

def process_public_chat(user_message, session_id):
    current_time = time.time()
    clean_old_sessions(current_time)

    session_data = active_sessions_public.get(session_id)

    if session_data:
        if current_time - session_data['last_active'] < 5:
            return {
                "message": "Heeh! Jangan nyepam dong! Servernya bisa meledak tahu! Tunggu bentar kek!",
                "expression": "angry"
            }
    else:
        session_data = {'history': [], 'last_active': current_time}
        active_sessions_public[session_id] = session_data

    active_sessions_public[session_id]['last_active'] = current_time

    dynamic_prompt = f"Pengunjung: {user_message}\nHersi:"
    session_data['history'].append({"role": "user", "content": dynamic_prompt})
    session_data['history'] = session_data['history'][-MAX_HISTORY_PUBLIC:]

    try:
        response = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[{"role": "system", "content": PROMPT_PUBLIC}] + session_data['history'],
            temperature=0.6,
            response_format={"type": "json_object"},
            max_tokens=MAX_TOKENS_PUBLIC,
        )

        reply_content = response.choices[0].message.content.strip()
        session_data['history'].append({"role": "assistant", "content": reply_content})
        
        return json.loads(reply_content)

    except Exception:
        if session_data['history'] and session_data['history'][-1]["role"] == "user":
            session_data['history'].pop()
        return {
            "message": "Hmph! Tante lagi males ngomong, servernya lagi sibuk tahu! Coba lagi nanti!",
            "expression": "baozhen"
        }

def get_datetime_context():
    now = datetime.now()
    hour = now.hour

    if 5 <= hour < 12:
        greeting = "pagi"
    elif 12 <= hour < 15:
        greeting = "siang"
    elif 15 <= hour < 18:
        greeting = "sore"
    else:
        greeting = "malam"

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
    dynamic_prompt = f"Data Server: {context_str}\n\nArka: {user_message}\nHersi:"

    if len(conversation_history_dashboard) >= MAX_HISTORY_DASHBOARD:
        conversation_history_dashboard = conversation_history_dashboard[-MAX_HISTORY_DASHBOARD:]

    conversation_history_dashboard.append({"role": "user", "content": dynamic_prompt})

    try:
        response = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[
                {"role": "system", "content": PROMPT_DASHBOARD},
                *conversation_history_dashboard
            ],
            temperature=0.4,
            response_format={"type": "json_object"},
            max_tokens=512,
        )

        reply_content = response.choices[0].message.content.strip()
        conversation_history_dashboard.append({"role": "assistant", "content": reply_content})

        return json.loads(reply_content)

    except Exception as e:
        print(f"\n[Hersi Error] Gagal memparsing respons: {e}\n", flush=True)
        return {
            "action": "CHAT",
            "message": "Hmph! Tante lagi pusing mikirin kerjaan lain, Arka jangan ganggu dulu deh!",
            "delay_minutes": 0
        }

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
    print("[Hersi] Riwayat percakapan direset.", flush=True)