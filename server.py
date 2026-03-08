import yt_dlp
import urllib.request
import json
import os
from fastapi import FastAPI, HTTPException

app = FastAPI(title="NeoMusic Backend")

stream_cache = {}
lyrics_cache = {}

YDL_OPTIONS = {
    'format': 'bestaudio/best',
    'noplaylist': True,
    'quiet': True,
    'skip_download': True,
    'extract_flat': False
}

@app.get("/api/stream")
def get_stream(q: str):
    if q in stream_cache:
        return {"stream_url": stream_cache[q]}

    search_query = f"scsearch1:{q}"
    try:
        with yt_dlp.YoutubeDL(YDL_OPTIONS) as ydl:
            info = ydl.extract_info(search_query, download=False)
        if not info or 'entries' not in info or not info['entries']:
            raise HTTPException(status_code=404, detail="Песня не найдена")
        
        audio_url = info['entries'][0].get('url')
        stream_cache[q] = audio_url
        return {"stream_url": audio_url}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/lyrics")
def get_lyrics(artist: str, title: str):
    query = f"{artist} {title}"
    if query in lyrics_cache:
        return {"lyrics": lyrics_cache[query]}

    # БЕРЕМ КЛЮЧ ИЗ СЕКРЕТОВ RENDER (ЕГО БОЛЬШЕ НЕТ В КОДЕ!)
    api_key = os.environ.get("GEMINI_API_KEY")
    
    if not api_key:
        return {"lyrics": "Ошибка: Ключ API не настроен на сервере."}

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"

    prompt = f"Напиши текст песни {artist} - {title}. Отправь ТОЛЬКО текст песни, без аккордов и комментариев. Если песня инструментальная, ответь 'Текст не найден'."
    data = {"contents": [{"parts": [{"text": prompt}]}]}

    try:
        req = urllib.request.Request(url, data=json.dumps(data).encode('utf-8'), headers={'Content-Type': 'application/json'})
        with urllib.request.urlopen(req) as response:
            result = json.loads(response.read().decode())
            text = result.get('candidates', [{}])[0].get('content', {}).get('parts', [{}])[0].get('text', 'Текст не найден.')
            
            lyrics_cache[query] = text.strip()
            return {"lyrics": text.strip()}
    except Exception as e:
        return {"lyrics": "Текст не найден (Ошибка сервера)."}

@app.get("/")
def root():
    return {"status": "NeoMusic Server API is running securely!"}
