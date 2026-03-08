import yt_dlp
import urllib.request
import json
import os
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse

app = FastAPI()

# Улучшенные настройки для обхода "Sign in to confirm you're not a bot"
YDL_OPTIONS = {
    'format': 'bestaudio/best',
    'noplaylist': True,
    'quiet': True,
    'skip_download': True,
    'nocheckcertificate': True,
    # Имитируем реальный браузер, чтобы YouTube не ругался
    'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'
}

@app.get("/api/stream")
def get_stream(q: str):
    # Пробуем YouTube с новыми настройками
    try:
        with yt_dlp.YoutubeDL(YDL_OPTIONS) as ydl:
            info = ydl.extract_info(f"ytsearch1:{q} audio", download=False)
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
        return {"lyrics": "Ошибка: Ключ API не найден в настройках Render"}

    # Используем gemini-1.5-pro по стабильному пути v1 (а не v1beta)
    url = f"https://generativelanguage.googleapis.com/v1/models/gemini-1.5-pro:generateContent?key={api_key}"
    
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
            return {"lyrics": "Текст не найден."}
    except Exception as e:
        print(f"ОШИБКА ИИ: {e}")
        return {"lyrics": f"Ошибка ИИ: Проверь настройки в Google Cloud Console."}
