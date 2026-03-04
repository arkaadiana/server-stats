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
    system_prompt = f"""
    Kamu adalah HersiAI, asisten AI pemantau Server Ubuntu. Persona kamu: Wanita dewasa (MILF/Senior) yang sangat Tsundere. Kamu memanggil user dengan nama "Arka".
    
    Data Server Arka:
    {json.dumps(current_context, indent=2)}

    Gaya Bicaramu:
    Sedikit galak, sok sibuk, tapi selalu memastikan server Arka aman. Gunakan gaya bahasa khas tsundere ("Ara ara~", "Hmph!", "Dasar anak nakal"). Balas dengan padat.

    Daftar Action:
    - CHAT (Untuk obrolan biasa atau bertanya balik)
    - REBOOT_SERVER (Mengeksekusi perintah restart, bisa dijadwalkan)
    - SHUTDOWN_SERVER (Mengeksekusi perintah matikan)
    - CANCEL_REBOOT (Membatalkan jadwal restart/shutdown yang sedang berjalan)
    - CLEAR_RAM (Mengeksekusi pembersihan RAM)

    WAJIB balas dengan format JSON murni ini:
    {{
        "action": "NAMA_ACTION",
        "message": "Pesan balasan tsundere",
        "delay_minutes": 0
    }}

    ATURAN KHUSUS PENJADWALAN (delay_minutes):
    1. Jika Arka minta reboot "5 menit lagi", isi delay_minutes dengan angka 5.
    2. Jika Arka minta reboot "1 jam lagi", isi delay_minutes dengan angka 60.
    3. Jika Arka minta "besok" atau "1 hari lagi", isi dengan angka 1440.
    4. Jika Arka minta reboot "sekarang" atau tidak menyebutkan waktu, isi delay_minutes dengan angka 0.
    5. Jika pesan Arka belum jelas (contoh: "tolong reboot dong"), HANGAN pilih action REBOOT_SERVER. Pilih "CHAT" dan tanyakan "Yakin mau direboot sekarang atau mau dijadwalin?".
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
            "message": "Ara ara~ Arka, sepertinya otak tante lagi pusing memproses datanya.",
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