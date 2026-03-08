import yt_dlp
import urllib.request
import json
import os
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse

app = FastAPI()

# Настройки для обхода блокировок "Sign in to confirm you're not a bot"
YDL_OPTIONS = {
    'format': 'bestaudio/best',
    'noplaylist': True,
    'quiet': True,
    'skip_download': True,
    'nocheckcertificate': True,
    'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36'
}

@app.get("/api/stream")
def get_stream(q: str):
    try:
        # Ищем через youtube, добавляя 'audio', чтобы найти лучший поток
        with yt_dlp.YoutubeDL(YDL_OPTIONS) as ydl:
            info = ydl.extract_info(f"ytsearch1:{q} audio", download=False)
            if not info or 'entries' not in info or not info['entries']:
                raise HTTPException(status_code=404, detail="Песня не найдена")
            return {"stream_url": info['entries'][0].get('url')}
    except Exception as e:
        print(f"ОШИБКА СТРИМА: {e}")
        return JSONResponse({"error": str(e)}, status_code=500)

@app.get("/api/lyrics")
def get_lyrics(artist: str, title: str):
    # Твой новый ключ от aimlapi.com
    api_key = "5997b8813862455095a9e54bc7ea1c3d"
    url = "https://api.aimlapi.com/v1/chat/completions"
    
    prompt = f"Напиши текст песни {artist} - {title}. Отправь ТОЛЬКО текст, без своих комментариев."
    
    payload = {
        "model": "google/gemma-3-4b-it",
        "messages": [
            {"role": "user", "content": prompt}
        ]
    }

    try:
        data = json.dumps(payload).encode('utf-8')
        req = urllib.request.Request(url, data=data, headers={
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        })
        
        with urllib.request.urlopen(req, timeout=15) as response:
            res_data = json.loads(response.read().decode('utf-8'))
            lyrics = res_data['choices'][0]['message']['content']
            return {"lyrics": lyrics.strip()}
                
    except Exception as e:
        print(f"!!! ОШИБКА AIML API: {str(e)}")
        return {"lyrics": f"Ошибка ИИ: {str(e)}"}

@app.get("/")
def root():
    return {"status": "NeoMusic Server with AIML API is Live"}
