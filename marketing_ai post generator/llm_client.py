import os
import requests
from dotenv import load_dotenv

# تحميل متغيرات البيئة
load_dotenv()

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
API_KEY = os.getenv("OPENROUTER_API_KEY")

def generate_marketing_post(prompt: str) -> str:
    """
    Function to call OpenRouter/GPT-4o-mini API
    ويجيب نص تسويقي حسب البرومبت اللي اتبعت.
    """
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "http://localhost",
        "X-Title": "Marketing AI Engine"
    }

    payload = {
        "model": "openai/gpt-4o-mini",
        "messages": [
            {"role": "system", "content": "You are an expert marketing copywriter."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.7
    }

    response = requests.post(OPENROUTER_URL, json=payload, headers=headers)
    response.raise_for_status()
    data = response.json()

    # ترجّع أول رد من الموديل
    return data["choices"][0]["message"]["content"]
