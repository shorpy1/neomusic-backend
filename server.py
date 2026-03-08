import yt_dlp
import urllib.request
import json
import os
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse

app = FastAPI()

# Ультимативные настройки для обхода обрывов связи
YDL_OPTIONS = {
    'format': 'bestaudio[ext=m4a]/bestaudio/best', # Форсируем формат m4a, который iOS AVPlayer держит идеально
    'noplaylist': True,
    'quiet': True,
    'skip_download': True,
    'nocheckcertificate': True,
    # Притворяемся Айфоном, чтобы YouTube не обрывал соединение
    'user_agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Mobile/15E148 Safari/604.1'
}

@app.get("/api/stream")
def get_stream(q: str):
    try:
        with yt_dlp.YoutubeDL(YDL_OPTIONS) as ydl:
            info = ydl.extract_info(f"ytsearch1:{q} audio", download=False)
            if not info or 'entries' not in info or not info['entries']:
                raise HTTPException(status_code=404, detail="Трек не найден")
            
            return {"stream_url": info['entries'][0].get('url')}
    except Exception as e:
        print(f"ОШИБКА СТРИМА: {e}")
        return JSONResponse({"error": str(e)}, status_code=500)

@app.get("/api/lyrics")
def get_lyrics(artist: str, title: str):
    api_key = os.environ.get("OPENROUTER_API_KEY", "").strip()
    if not api_key:
        return {"lyrics": "Ошибка: Добавь OPENROUTER_API_KEY в настройки Render"}

    # Используем OpenRouter API
    url = "https://openrouter.ai/api/v1/chat/completions"
    prompt = f"Напиши только текст песни {artist} - {title}. Без аккордов и твоих комментариев."
    
    payload = {
        "model": "google/gemini-pro", # Бесплатная и стабильная модель в OpenRouter
        "messages": [
            {"role": "user", "content": prompt}
        ]
    }

    try:
        req = urllib.request.Request(
            url, 
            data=json.dumps(payload).encode('utf-8'), 
            headers={
                'Authorization': f'Bearer {api_key}', # Авторизация OpenRouter
                'Content-Type': 'application/json',
                'HTTP-Referer': 'https://neomusic-api.onrender.com' # OpenRouter просит URL сайта
            }
        )
        with urllib.request.urlopen(req, timeout=15) as response:
            res = json.loads(response.read().decode('utf-8'))
            text = res['choices'][0]['message']['content']
            return {"lyrics": text.strip()}
            
    except Exception as e:
        print(f"ОШИБКА ИИ: {e}")
        return {"lyrics": f"Ошибка ИИ: {str(e)}"}

@app.get("/")
def root():
    return {"status": "NeoMusic Ultimate Fix is Live"}
