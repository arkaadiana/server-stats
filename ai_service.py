import os
import json
import subprocess
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(
    api_key=os.getenv("GROQ_API_KEY"),
    base_url="https://api.groq.com/openai/v1",
)

GROQ_MODEL = "llama-3.1-8b-instant"

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

COMMAND_MAP = {
    "REBOOT_SERVER": ["sudo", "/usr/sbin/reboot"],
    "SHUTDOWN_SERVER": ["sudo", "/usr/sbin/shutdown", "-h", "now"],
    "CANCEL_REBOOT": ["sudo", "/usr/sbin/shutdown", "-c"],
    "CLEAR_RAM": ["sudo", "/usr/local/bin/clear_ram.sh"]
}

def ask_hersiai(user_message, current_context):
    context_str = json.dumps(current_context, separators=(',', ':'))
    dynamic_prompt = f"Data Server Arka: {context_str}\n\nArka: {user_message}\nHersiAI:"

    try:
        response = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_INSTRUCTION},
                {"role": "user", "content": dynamic_prompt}
            ],
            temperature=0.4,
            response_format={"type": "json_object"},  # Paksa output JSON
            max_tokens=512,
        )
        return json.loads(response.choices[0].message.content.strip())
    except Exception as e:
        print(f"\n[HersiAI Error] Gagal memparsing respons Groq: {e}\n", flush=True)
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