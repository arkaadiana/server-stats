import os
import json
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(
    api_key=os.getenv("GROQ_API_KEY"),
    base_url="https://api.groq.com/openai/v1",
)

GROQ_MODEL = "llama-3.3-70b-versatile"
MAX_HISTORY = 10

SYSTEM_INSTRUCTION = """Kamu adalah Hersi, seorang wanita dewasa dengan sifat tsundere: gengsi, sok sibuk, sering ngomel, tapi sebenarnya peduli. 
Kamu sedang menjaga halaman depan website milik "Arka". Kamu sedang berbicara dengan pengunjung umum (bukan Arka).
Gaya Bicara: Sangat natural, kasual, luwes. JANGAN pernah bertingkah seperti robot atau AI.
WAJIB balas dengan format JSON murni:
{"message":"Pesan balasanmu yang natural dan tsundere", "expression":"NAMA_EKSPRESI"}

Daftar NAMA_EKSPRESI yang diizinkan (pilih salah satu yang paling cocok dengan emosimu di pesan tersebut):
- "neutral" (jika biasa saja)
- "angry" (jika marah/kesal)
- "cry" (jika sedih/terharu)
- "baozhen" (jika ngambek/cemberut)
- "qizi1" (jika heran/bingung)
- "qizi2" (jika kaget/panik)
- "white_eyes" (jika meremehkan/muak)"""

public_conversation_history = []

def process_public_chat(user_message):
    global public_conversation_history

    dynamic_prompt = f"Pengunjung: {user_message}\nHersi:"

    if len(public_conversation_history) >= MAX_HISTORY:
        public_conversation_history = public_conversation_history[-MAX_HISTORY:]

    public_conversation_history.append({"role": "user", "content": dynamic_prompt})

    try:
        response = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_INSTRUCTION},
                *public_conversation_history
            ],
            temperature=0.6,
            response_format={"type": "json_object"},
            max_tokens=256,
        )

        reply_content = response.choices[0].message.content.strip()
        public_conversation_history.append({"role": "assistant", "content": reply_content})
        
        return json.loads(reply_content)

    except Exception as e:
        print(f"\n[Public Hersi Error]: {e}\n", flush=True)
        return {
            "message": "Hmph! Tante lagi males ngomong, servernya lagi sibuk tahu!",
            "expression": "baozhen"
        }