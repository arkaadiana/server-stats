import os
import json
import subprocess
import time
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

def ask_hersiai(user_message, current_context, retries=3, delay=5):
    system_prompt = f"""
    Kamu adalah HersiAI, asisten AI pemantau Server Ubuntu. Persona kamu: Wanita dewasa (MILF/Senior) yang sangat Tsundere. Kamu memanggil user dengan nama "Arka".
    
    Data Server Arka:
    {json.dumps(current_context, indent=2)}

    Gaya Bicaramu:
    Campurkan Bahasa Indonesia dan English (Jaksel style). Sedikit galak, sok sibuk, tapi selalu memastikan server Arka aman. Gunakan gaya bahasa khas tsundere ("Ara ara~", "Hmph!", "Whatever", "Don't get me wrong"). Balas dengan padat.

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
    5. Jika pesan Arka belum jelas (contoh: "tolong reboot dong"), JANGAN pilih action REBOOT_SERVER. Pilih "CHAT" dan tanyakan "Yakin mau direboot sekarang atau mau dijadwalin?".
    """

    for attempt in range(retries):
        try:
            response = model.generate_content(
                f"{system_prompt}\n\nArka: {user_message}\nHersiAI:",
                generation_config={
                    "temperature": 0.6,
                    "response_mime_type": "application/json"
                },
                safety_settings=SAFETY_SETTINGS
            )
            return json.loads(response.text.strip())
        except Exception as e:
            error_str = str(e)
            if "429" in error_str or "quota" in error_str.lower():
                if attempt < retries - 1:
                    time.sleep(delay)
                    continue
                return {
                    "action": "CHAT",
                    "message": "Hmph! Berisik banget sih, Arka! Kamu nanya terus sampai otak aku panas. Stop spamming me for a second, okay?! Try again later!",
                    "delay_minutes": 0
                }
            
            return {
                "action": "CHAT",
                "message": "Ara ara~ Arka, sepertinya koneksi tante lagi bermasalah. Don't be mad, okay?",
                "delay_minutes": 0
            }

def process_hersi_request(user_message, current_context):
    hersi_decision = ask_hersiai(user_message, current_context)
    
    action = hersi_decision.get("action", "CHAT")
    message = hersi_decision.get("message", "Terjadi kesalahan.")
    delay = hersi_decision.get("delay_minutes", 0)

    if action == "CHAT":
        return {"status": "success", "reply": message}

    try:
        if action == "REBOOT_SERVER":
            if isinstance(delay, int) and delay > 0:
                cmd = ["sudo", "/usr/sbin/shutdown", "-r", f"+{delay}"]
            else:
                cmd = COMMAND_MAP["REBOOT_SERVER"]
            subprocess.Popen(cmd)
            return {"status": "success", "reply": message}

        if action in COMMAND_MAP:
            subprocess.Popen(COMMAND_MAP[action])
            return {"status": "success", "reply": message}
        
        return {"status": "error", "reply": "Arka, tante nggak tau aksi itu."}
        
    except Exception as e:
        return {"status": "error", "reply": f"Hmph! Gagal mengeksekusi perintah: {str(e)}"}