import yt_dlp
import urllib.request
import json
import os
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse

app = FastAPI()

# YouTube поиск работает намного стабильнее SoundCloud
YDL_OPTIONS = {
    'format': 'bestaudio/best',
    'noplaylist': True,
    'quiet': True,
    'skip_download': True,
}

@app.get("/api/stream")
def get_stream(q: str):
    # Теперь ищем в YouTube (ytsearch) вместо SoundCloud
    search_query = f"ytsearch1:{q}"
    try:
        with yt_dlp.YoutubeDL(YDL_OPTIONS) as ydl:
            info = ydl.extract_info(search_query, download=False)
        if not info or 'entries' not in info or not info['entries']:
            raise HTTPException(status_code=404, detail="Песня не найдена")
        
        audio_url = info['entries'][0].get('url')
        return {"stream_url": audio_url}
    except Exception as e:
        print(f"ОШИБКА СТРИМА: {e}")
        return JSONResponse({"error": str(e)}, status_code=500)

@app.get("/api/lyrics")
def get_lyrics(artist: str, title: str):
    api_key = os.environ.get("GEMINI_API_KEY", "").strip()
    if not api_key:
        return {"lyrics": "Ошибка: Добавь GEMINI_API_KEY в настройки Render"}

    # Используем модель gemini-pro — она самая стабильная и не выдает 404
    url = f"https://generativelanguage.googleapis.com/v1/models/gemini-pro:generateContent?key={api_key}"
    
    prompt = f"Write ONLY the lyrics for the song: {artist} - {title}. No comments, no chords."
    data = {"contents": [{"parts": [{"text": prompt}]}]}
    
    try:
        req = urllib.request.Request(
            url, 
            data=json.dumps(data).encode('utf-8'), 
            headers={'Content-Type': 'application/json'}
        )
        with urllib.request.urlopen(req, timeout=15) as response:
            res = json.loads(response.read().decode('utf-8'))
            if 'candidates' in res and res['candidates']:
                text = res['candidates'][0]['content']['parts'][0]['text']
                return {"lyrics": text.strip()}
            else:
                return {"lyrics": "Текст не найден нейросетью."}
    except Exception as e:
        print(f"ОШИБКА ИИ: {e}")
        return {"lyrics": f"Ошибка ИИ. Проверь настройки проекта Google Cloud."}

@app.get("/")
def root():
    return {"status": "NeoMusic Server is Fixed!"}
