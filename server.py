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

    # Пробуем несколько вариантов моделей (одна точно сработает!)
    models = ["gemini-1.5-flash-latest", "gemini-1.5-flash", "gemini-pro"]
    
    prompt = f"Напиши текст песни {artist} - {title}. Отправь ТОЛЬКО текст песни, без аккордов и комментариев."
    data = {"contents": [{"parts": [{"text": prompt}]}]}
    
    last_error = ""
    
    for model in models:
        # Используем v1beta, так как она самая гибкая
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
        
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
        except Exception as e:
            last_error = str(e)
            continue # Пробуем следующую модель в списке
            
    return {"lyrics": f"ИИ не смог найти слова. Последняя ошибка: {last_error}"}

@app.get("/")
def root():
    return {"status": "NeoMusic Server is ready!"}
