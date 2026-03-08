import yt_dlp
import urllib.request
import json
import os
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse

app = FastAPI()

# Усиленная имитация браузера для обхода блокировки "Sign in to confirm you're not a bot"
YDL_OPTIONS = {
    'format': 'bestaudio/best',
    'noplaylist': True,
    'quiet': True,
    'skip_download': True,
    'nocheckcertificate': True,
    'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36',
    'referer': 'https://www.google.com/'
}

@app.get("/api/stream")
def get_stream(q: str):
    try:
        # Добавляем "lyrics" к поиску, это часто помогает найти официальные аудио-видео
        search_query = f"ytsearch1:{q} official audio"
        with yt_dlp.YoutubeDL(YDL_OPTIONS) as ydl:
            info = ydl.extract_info(search_query, download=False)
            if not info or 'entries' not in info or not info['entries']:
                raise HTTPException(status_code=404, detail="Песня не найдена")
            return {"stream_url": info['entries'][0].get('url')}
    except Exception as e:
        print(f"ОШИБКА СТРИМА: {e}")
        return JSONResponse({"error": str(e)}, status_code=500)

@app.get("/api/lyrics")
def get_lyrics(artist: str, title: str):
    api_key = os.environ.get("GEMINI_API_KEY", "").strip()
    if not api_key:
        return {"lyrics": "Ошибка: Ключ API не настроен в Render"}

    # Самый стабильный путь для ключей из AI Studio
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
    prompt = f"Write ONLY the lyrics for: {artist} - {title}. No chords, no intro text."
    data = {"contents": [{"parts": [{"text": prompt}]}]}

    try:
        req = urllib.request.Request(url, data=json.dumps(data).encode('utf-8'), headers={'Content-Type': 'application/json'})
        with urllib.request.urlopen(req, timeout=15) as response:
            res = json.loads(response.read().decode('utf-8'))
            text = res['candidates'][0]['content']['parts'][0]['text']
            return {"lyrics": text.strip()}
    except Exception as e:
        print(f"ОШИБКА ИИ: {e}")
        return {"lyrics": f"Ошибка ИИ: Убедись, что ограничения ключа стоят в 'None'"}

@app.get("/")
def root():
    return {"status": "NeoMusic Server Updated"}
