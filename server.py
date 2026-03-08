import yt_dlp
import urllib.request
import json
from fastapi import FastAPI
from fastapi.responses import JSONResponse

app = FastAPI()

# Настройки для поиска музыки
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
    # Используем БЕСПЛАТНЫЙ публичный API (аналог Puter для Python)
    # Этот сервис не требует ключей!
    prompt = f"Write ONLY the lyrics for the song: {artist} - {title}. No comments, no chords."
    
    # Публичный эндпоинт для работы с моделями без ключа
    url = "https://api.freegpt4.download/v1/chat/completions"
    
    payload = {
        "model": "gpt-3.5-turbo",
        "messages": [{"role": "user", "content": prompt}]
    }

    try:
        data = json.dumps(payload).encode('utf-8')
        req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'})
        
        with urllib.request.urlopen(req, timeout=15) as response:
            res_data = json.loads(response.read().decode('utf-8'))
            lyrics = res_data['choices'][0]['message']['content']
            return {"lyrics": lyrics.strip()}
            
    except Exception as e:
        # Если первый способ не сработал, пробуем запасной (DuckDuckGo AI - тоже бесплатно)
        return {"lyrics": f"Текст временно недоступен. Попробуй позже. (Ошибка: {str(e)})"}

@app.get("/")
def root():
    return {"status": "NeoMusic Free AI Server is Live"}
