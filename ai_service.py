import os
import json
import subprocess
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold
from dotenv import load_dotenv

load_dotenv()

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel('gemini-2.5-flash')

COMMAND_MAP = {
    "REBOOT_SERVER": ["sudo", "/usr/sbin/reboot"],
    "SHUTDOWN_SERVER": ["sudo", "/usr/sbin/shutdown", "-h", "now"],
    "CLEAR_RAM": ["sudo", "/usr/local/bin/clear_ram.sh"]
}

SAFETY_SETTINGS = {
    HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
}

def ask_hersiai(user_message, current_context):
    system_prompt = f"""
    Kamu adalah HersiAI, asisten AI pemantau Server Ubuntu. Persona kamu: Wanita dewasa (MILF/Senior) yang sangat Tsundere. Kamu memanggil user dengan nama "Arka".
    
    Data Server Arka:
    {json.dumps(current_context, indent=2)}

    Gaya Bicaramu:
    Sedikit galak, sok sibuk, tapi selalu memastikan server Arka aman. Gunakan gaya bahasa khas tsundere ("Ara ara~", "Hmph!", "Dasar anak nakal"). Balas dengan padat.

    Daftar Action:
    - CHAT (Untuk obrolan biasa atau bertanya balik)
    - REBOOT_SERVER (Mengeksekusi perintah restart)
    - SHUTDOWN_SERVER (Mengeksekusi perintah matikan)
    - CLEAR_RAM (Mengeksekusi pembersihan RAM)

    WAJIB balas dengan format JSON murni ini (TANPA need_confirm):
    {{
        "action": "NAMA_ACTION",
        "message": "Pesan balasan tsundere"
    }}

    ATURAN EKSEKUSI REBOOT/SHUTDOWN:
    1. Jika pesan Arka hanya "reboot server" atau "restart", JANGAN langsung action REBOOT_SERVER. Gunakan action "CHAT" dan balas "Yakin mau direboot sekarang?".
    2. Jika pesan Arka sudah JELAS menyuruh dan mengkonfirmasi (contoh: "iya tolong reboot", "yakin restart", "reboot sekarang aja"), BARU kamu boleh menggunakan action "REBOOT_SERVER".
    """

    try:
        response = model.generate_content(
            f"{system_prompt}\n\nArka: {user_message}\nHersiAI:",
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
            "message": "Ara ara~ Arka, sepertinya otak tante lagi pusing memproses datanya."
        }

def process_hersi_request(user_message, current_context):
    hersi_decision = ask_hersiai(user_message, current_context)
    
    action = hersi_decision.get("action", "CHAT")
    message = hersi_decision.get("message", "Terjadi kesalahan.")

    if action == "CHAT":
        return {"status": "success", "reply": message}

    if action in COMMAND_MAP:
        try:
            subprocess.Popen(COMMAND_MAP[action])
            return {"status": "success", "reply": message}
        except Exception as e:
            return {"status": "error", "reply": f"Hmph! Gagal mengeksekusi perintah: {str(e)}"}
    else:
        return {"status": "error", "reply": "Arka, tante nggak tau aksi itu."}