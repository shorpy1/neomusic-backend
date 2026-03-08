import yt_dlp
import urllib.request
import json
import os
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse

app = FastAPI()

YDL_OPTIONS = {'format': 'bestaudio/best', 'noplaylist': True, 'quiet': True}

@app.get("/api/stream")
def get_stream(q: str):
    try:
        with yt_dlp.YoutubeDL(YDL_OPTIONS) as ydl:
            info = ydl.extract_info(f"scsearch1:{q}", download=False)
            url = info['entries'][0].get('url')
            return {"stream_url": url}
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)

@app.get("/api/lyrics")
def get_lyrics(artist: str, title: str):
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        return {"lyrics": "Ошибка: Ключ API не найден в настройках Render"}

    # Пробуем ВСЕ комбинации версий и моделей
    versions = ["v1", "v1beta"]
    models = ["gemini-1.5-flash", "gemini-1.5-flash-latest", "gemini-pro"]
    
    prompt = f"Напиши текст песни {artist} - {title}. Отправь ТОЛЬКО текст песни, без аккордов и комментариев."
    data = {"contents": [{"parts": [{"text": prompt}]}]}
    
    for ver in versions:
        for model in models:
            url = f"https://generativelanguage.googleapis.com/{ver}/models/{model}:generateContent?key={api_key}"
            try:
                req = urllib.request.Request(
                    url, 
                    data=json.dumps(data).encode('utf-8'), 
                    headers={'Content-Type': 'application/json'}
                )
                with urllib.request.urlopen(req, timeout=10) as response:
                    res = json.loads(response.read().decode('utf-8'))
                    if 'candidates' in res and res['candidates']:
                        text = res['candidates'][0]['content']['parts'][0]['text']
                        return JSONResponse(content={"lyrics": text.strip()})
            except:
                continue # Если эта пара (версия/модель) не подошла, пробуем следующую
            
    return {"lyrics": "ИИ не смог найти слова. Попробуй позже."}

@app.get("/")
def root():
    return {"status": "NeoMusic Server is ready!"}
