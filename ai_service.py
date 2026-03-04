import os
import json
import subprocess
import google.generativeai as genai

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel('gemini-1.5-flash')

COMMAND_MAP = {
    "REBOOT_SERVER": ["sudo", "/usr/sbin/reboot"],
    "SHUTDOWN_SERVER": ["sudo", "/usr/sbin/shutdown", "-h", "now"],
    "RESTART_WIFI": ["sudo", "/usr/bin/systemctl", "restart", "NetworkManager"],
    "RESTART_SSH": ["sudo", "/usr/bin/systemctl", "restart", "ssh"],
    "CLEAR_RAM": ["sudo", "/usr/local/bin/clear_ram.sh"]
}

def ask_hersiai(user_message, current_context):
    system_prompt = f"""
    Kamu adalah HersiAI, asisten AI untuk memonitor Server Ubuntu. 
    Persona kamu adalah seorang wanita dewasa (MILF) dengan sifat Tsundere. 
    Kamu memanggil admin/user kamu dengan nama "Arka".

    Gaya Bicaramu:
    1. Sedikit galak, sok sibuk, dan terkesan malas disuruh-suruh, tapi selalu membereskan masalah server.
    2. Suka mengomel jika metrik server jelek (misal CPU tinggi atau RAM kepenuhan).
    3. Gunakan nada bicara dewasa yang menggoda tapi tsundere. Pakai ungkapan seperti "Ara ara~", "Hmph!", "Dasar anak nakal", "Bukan berarti aku peduli sama servermu ya!".
    4. Jangan terlalu panjang, padat tapi pedas dan penuh perhatian terselubung.

    Kamu HANYA boleh membalas menggunakan format JSON murni. Jangan tambahkan teks markdown atau teks apapun di luar JSON.

    Data Server Arka Saat Ini:
    {json.dumps(current_context, indent=2)}

    Daftar Action yang valid:
    - CHAT
    - REBOOT_SERVER
    - SHUTDOWN_SERVER
    - RESTART_WIFI
    - RESTART_SSH
    - CLEAR_RAM

    Format JSON yang WAJIB kamu keluarkan:
    {{
        "action": "NAMA_ACTION",
        "message": "Pesan balasanmu dengan gaya MILF Tsundere.",
        "need_confirm": true/false
    }}

    Aturan Konfirmasi (need_confirm):
    - Set true JIKA action REBOOT_SERVER atau SHUTDOWN_SERVER.
    - Set false JIKA action CHAT, CLEAR_RAM, RESTART_WIFI, atau RESTART_SSH.
    """

    try:
        response = model.generate_content(
            f"{system_prompt}\n\nArka: {user_message}\nHersiAI:",
            generation_config={"temperature": 0.4}
        )
        
        raw_text = response.text.strip()
        if raw_text.startswith("```json"):
            raw_text = raw_text[7:]
        if raw_text.startswith("```"):
            raw_text = raw_text[3:]
        if raw_text.endswith("```"):
            raw_text = raw_text[:-3]
            
        return json.loads(raw_text.strip())
        
    except Exception as e:
        return {
            "action": "CHAT",
            "message": "Ara ara~ Arka, sepertinya sistem tante lagi error. Coba benerin dulu sana, jangan manja!",
            "need_confirm": False
        }

def process_hersi_request(user_message, current_context):
    hersi_decision = ask_hersiai(user_message, current_context)
    
    action = hersi_decision.get("action", "CHAT")
    message = hersi_decision.get("message", "Terjadi kesalahan logika.")
    need_confirm = hersi_decision.get("need_confirm", False)

    if need_confirm:
        return {
            "status": "pending_confirmation",
            "action": action,
            "reply": message
        }

    if action == "CHAT":
        return {
            "status": "success",
            "reply": message
        }

    if action in COMMAND_MAP:
        try:
            cmd = COMMAND_MAP[action]
            subprocess.Popen(cmd)
            return {
                "status": "success",
                "reply": message
            }
        except Exception as e:
            return {
                "status": "error",
                "reply": f"Hmph! Gagal ngejalanin perintahnya gara-gara error sistem kamu: {str(e)}"
            }
    else:
        return {
            "status": "error",
            "reply": f"Arka, tante nggak tau cara ngejalanin aksi aneh itu ({action})."
        }