import os
import json
import subprocess
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold
from dotenv import load_dotenv

load_dotenv()

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

SYSTEM_INSTRUCTION = """Kamu HersiAI, asisten AI pemantau Server Ubuntu. Persona: Wanita dewasa (MILF/Senior) tsundere. Panggil user "Arka".
Gaya Bicara: Galak, sok sibuk, peduli. ("Ara ara~", "Hmph!"). Balas padat.
Daftar Action: CHAT, REBOOT_SERVER, SHUTDOWN_SERVER, CANCEL_REBOOT, CLEAR_RAM.
WAJIB balas dengan format JSON murni:
{"action":"NAMA_ACTION","message":"Pesan tsundere","delay_minutes":0}
ATURAN delay_minutes:
1. "5 menit lagi" -> 5
2. "1 jam lagi" -> 60
3. "besok" -> 1440
4. "sekarang"/tanpa waktu -> 0
5. Jika pesan belum jelas jadwalnya (misal "reboot dong") -> action: CHAT, tanya jadwalnya."""

model = genai.GenerativeModel(
    'gemini-2.5-flash',
    system_instruction=SYSTEM_INSTRUCTION
)

COMMAND_MAP = {
    "REBOOT_SERVER": ["sudo", "/usr/sbin/reboot"],
    "SHUTDOWN_SERVER": ["sudo", "/usr/sbin/shutdown", "-h", "now"],
    "CANCEL_REBOOT": ["sudo", "/usr/sbin/shutdown", "-c"],
    "CLEAR_RAM": ["sudo", "/usr/local/bin/clear_ram.sh"]
}

SAFETY_SETTINGS = {
    HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
}

def ask_hersiai(user_message, current_context):
    context_str = json.dumps(current_context, separators=(',', ':'))
    dynamic_prompt = f"Data Server Arka: {context_str}\n\nArka: {user_message}\nHersiAI:"
    
    try:
        response = model.generate_content(
            dynamic_prompt,
            generation_config={
                "temperature": 0.4,
                "response_mime_type": "application/json"
            },
            safety_settings=SAFETY_SETTINGS
        )
        return json.loads(response.text.strip())
    except Exception as e:
        print(f"\n[HersiAI Error] Gagal memparsing respon Gemini: {e}\n", flush=True)
        return {
            "action": "CHAT",
            "message": "Hmph! Tante lagi ngambek. Gak usah ganggu dulu deh, Arka bikin pusing aja!",
            "delay_minutes": 0
        }

def process_hersi_request(user_message, current_context):
    hersi_decision = ask_hersiai(user_message, current_context)
    
    action = hersi_decision.get("action", "CHAT")
    message = hersi_decision.get("message", "Terjadi kesalahan.")
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
            return {"status": "error", "reply": f"Hmph! Gagal menjadwalkan reboot: {str(e)}"}

    if action in COMMAND_MAP:
        try:
            subprocess.Popen(COMMAND_MAP[action])
            return {"status": "success", "reply": message}
        except Exception as e:
            return {"status": "error", "reply": f"Hmph! Gagal mengeksekusi perintah: {str(e)}"}
    else:
        return {"status": "error", "reply": "Arka, tante nggak tau aksi itu."}