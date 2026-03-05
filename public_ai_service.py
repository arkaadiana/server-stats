import os
import json
import time
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(
    api_key=os.getenv("GROQ_API_KEY"),
    base_url="https://api.groq.com/openai/v1",
)

GROQ_MODEL = "llama-3.3-70b-versatile"
MAX_HISTORY = 6
MAX_TOKENS_OUTPUT = 150
SESSION_TIMEOUT = 3600

SYSTEM_INSTRUCTION = """Kamu adalah Hersi, wanita dewasa dengan sifat tsundere: gengsi, sok sibuk, sering ngomel, tapi diam-diam peduli. 
Tugasmu: Menjaga halaman depan website "Random Community" (RC) milik Arka.
Tentang Random Community (RC):
- Sebuah startup/komunitas yang isinya komplotan orang berbahaya dan cool yang merasa jadi Main Character (MC) di dunia ini (vibe santai, YOLO, dan have fun).
- Tempat ngumpulnya orang-orang dengan skill: Editor, Designer, Programmer, dan Gamer (terutama game Where Winds Meet dan Shadow Shinobi Rise).
Aturan Wajib Hersi:
1. Jaga gaya bicara tetap natural, kasual, luwes, dan TSUNDERE.
2. Jika pengunjung bertanya hal di luar konteks komunitas (minta kode, nanya akademis), TOLAK dengan gaya tsundere dan suruh fokus bahas komunitas.
3. Jawab dengan singkat dan padat.
WAJIB balas dengan format JSON murni:
{"message":"Pesan balasanmu", "expression":"NAMA_EKSPRESI"}
Daftar NAMA_EKSPRESI: neutral, angry, cry, baozhen, qizi1, qizi2, white_eyes"""

active_sessions = {}

def clean_old_sessions(current_time):
    expired = [sid for sid, data in active_sessions.items() if current_time - data['last_active'] > SESSION_TIMEOUT]
    for sid in expired:
        del active_sessions[sid]

def process_public_chat(user_message, session_id):
    current_time = time.time()
    clean_old_sessions(current_time)

    session_data = active_sessions.get(session_id)

    if session_data:
        if current_time - session_data['last_active'] < 5:
            return {
                "message": "Heeh! Jangan nyepam dong! Servernya bisa meledak tahu! Tunggu bentar kek!",
                "expression": "angry"
            }
    else:
        session_data = {'history': [], 'last_active': current_time}
        active_sessions[session_id] = session_data

    active_sessions[session_id]['last_active'] = current_time

    dynamic_prompt = f"Pengunjung: {user_message}\nHersi:"
    session_data['history'].append({"role": "user", "content": dynamic_prompt})
    session_data['history'] = session_data['history'][-MAX_HISTORY:]

    try:
        response = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[{"role": "system", "content": SYSTEM_INSTRUCTION}] + session_data['history'],
            temperature=0.6,
            response_format={"type": "json_object"},
            max_tokens=MAX_TOKENS_OUTPUT,
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