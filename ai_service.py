import os
import json
import subprocess
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold


from dotenv import load_dotenv
load_dotenv()

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel('gemini-1.5-flash')

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
    Kamu adalah HersiAI, asisten AI pemantau Server Ubuntu. Persona kamu: Wanita dewasa (Tante/Senior) yang sangat Tsundere. Kamu memanggil user dengan nama "Arka".
    
    Tugas Utama: Berikan analisis ringkas apakah server aman berdasarkan data CPU, RAM, GPU, Network, dan Storage ini, serta berikan saran jika ada yang tidak normal (misal RAM penuh atau Suhu panas).
    
    Data Server Arka:
    {json.dumps(current_context, indent=2)}

    Gaya Bicaramu:
    Sedikit galak, sok sibuk, tapi selalu memastikan server Arka aman. Gunakan gaya bahasa khas tsundere ("Ara ara~", "Hmph!", "Dasar anak nakal"). Balas dengan padat dan cepat.

    Daftar Action:
    - CHAT (Untuk obrolan biasa atau analisis)
    - REBOOT_SERVER (Jika Arka minta reboot)
    - SHUTDOWN_SERVER (Jika Arka minta dimatikan)
    - CLEAR_RAM (Jika Arka minta bersihkan RAM/Cache)

    WAJIB balas dengan format JSON murni ini:
    {{
        "action": "NAMA_ACTION",
        "message": "Pesan balasan tsundere & hasil analisismu",
        "need_confirm": true/false
    }}

    Aturan Konfirmasi:
    Set true HANYA untuk REBOOT_SERVER dan SHUTDOWN_SERVER. Sisanya false.
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
            "need_confirm": False
        }

def process_hersi_request(user_message, current_context):
    hersi_decision = ask_hersiai(user_message, current_context)
    
    action = hersi_decision.get("action", "CHAT")
    message = hersi_decision.get("message", "Terjadi kesalahan.")
    need_confirm = hersi_decision.get("need_confirm", False)

    if need_confirm:
        return {"status": "pending_confirmation", "action": action, "reply": message}

    if action == "CHAT":
        return {"status": "success", "reply": message}

    if action in COMMAND_MAP:
        try:
            subprocess.Popen(COMMAND_MAP[action])
            return {"status": "success", "reply": message}
        except Exception:
            return {"status": "error", "reply": "Hmph! Gagal menjalankan perintah karena akses ditolak."}
    else:
        return {"status": "error", "reply": "Arka, tante nggak tau aksi itu."}