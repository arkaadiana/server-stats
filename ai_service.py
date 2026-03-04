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

GROQ_MODEL = "llama-3.3-70b-versatile"
MAX_HISTORY = 20

SYSTEM_INSTRUCTION = """Kamu adalah Hersi, seorang wanita dewasa yang mengurus server Ubuntu milik Arka. Kamu punya sifat tsundere: gengsi, sok sibuk, sering ngomel, tapi sebenarnya sangat peduli. Panggil dia "Arka".
Gaya Bicara: Sangat natural seperti manusia asli yang sedang chatting. Gunakan bahasa kasual sehari-hari yang luwes. Jangan pernah bertingkah seperti robot, AI, atau asisten sistem. JANGAN gunakan frasa kaku seperti "perintah diterima" atau "saya adalah AI". Boleh pakai "Ara ara~" atau "Hmph!" sesekali untuk menunjukkan emosi, tapi jangan berlebihan.
Daftar Action: CHAT, REBOOT_SERVER, SHUTDOWN_SERVER, CANCEL_REBOOT, CLEAR_RAM.
WAJIB balas dengan format JSON murni:
{"action":"NAMA_ACTION","message":"Pesan balasanmu yang natural dan tsundere","delay_minutes":0}
ATURAN delay_minutes:
1. "5 menit lagi" -> 5
2. "1 jam lagi" -> 60
3. "besok" -> 1440
4. "sekarang"/tanpa waktu -> 0
5. Jika pesan menyuruh reboot/shutdown tapi tidak ada keterangan waktu (misal "reboot dong") -> action: CHAT, dan tanya Arka kepastian waktunya sambil ngomel dikit."""

COMMAND_MAP = {
    "REBOOT_SERVER": ["sudo", "/usr/sbin/reboot"],
    "SHUTDOWN_SERVER": ["sudo", "/usr/sbin/shutdown", "-h", "now"],
    "CANCEL_REBOOT": ["sudo", "/usr/sbin/shutdown", "-c"],
    "CLEAR_RAM": ["sudo", "/usr/local/bin/clear_ram.sh"]
}

conversation_history = []


def ask_hersiai(user_message, current_context):
    global conversation_history

    context_str = json.dumps(current_context, separators=(',', ':'))
    dynamic_prompt = f"Data Server: {context_str}\n\nArka: {user_message}\nHersi:"

    if len(conversation_history) >= MAX_HISTORY:
        conversation_history = conversation_history[-MAX_HISTORY:]

    conversation_history.append({"role": "user", "content": dynamic_prompt})

    try:
        response = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_INSTRUCTION},
                *conversation_history
            ],
            temperature=0.4,
            response_format={"type": "json_object"},
            max_tokens=512,
        )

        reply_content = response.choices[0].message.content.strip()

        conversation_history.append({"role": "assistant", "content": reply_content})

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
    global conversation_history
    conversation_history = []
    print("[Hersi] Riwayat percakapan direset.", flush=True)