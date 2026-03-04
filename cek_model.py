import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

print("Mencari daftar model yang diizinkan untuk API Key kamu...")
print("-" * 50)

try:
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            print(m.name)
    print("-" * 50)
    print("Selesai!")
except Exception as e:
    print(f"Error: {e}")