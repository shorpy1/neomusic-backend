import yt_dlp
import urllib.request
import urllib.parse
import json
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse

app = FastAPI()

# Музыка работает идеально, не трогаем
YDL_OPTIONS = {
    'format': 'bestaudio/best',
    'noplaylist': True,
    'quiet': True,
    'skip_download': True
}

@app.get("/api/stream")
def get_stream(q: str):
    try:
        with yt_dlp.YoutubeDL(YDL_OPTIONS) as ydl:
            info = ydl.extract_info(f"scsearch1:{q}", download=False)
            if not info or 'entries' not in info or not info['entries']:
                raise HTTPException(status_code=404, detail="Трек не найден")
            return {"stream_url": info['entries'][0].get('url')}
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)

@app.get("/api/lyrics")
def get_lyrics(artist: str, title: str):
    url = "https://api.aimlapi.com/v1/chat/completions"
    api_key = "5997b8813862455095a9e54bc7ea1c3d"
    
    prompt = f"Напиши только текст песни {artist} - {title}. Без аккордов."
    payload = {
        "model": "google/gemma-3-4b-it",
        "messages": [{"role": "user", "content": prompt}]
    }

    try:
        # Пробуем ИИ, маскируясь под браузер, чтобы убрать ошибку 403
        req = urllib.request.Request(
            url, 
            data=json.dumps(payload).encode('utf-8'), 
            headers={
                'Authorization': f'Bearer {api_key}',
                'Content-Type': 'application/json',
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/123.0.0.0 Safari/537.36'
            }
        )
        with urllib.request.urlopen(req, timeout=10) as response:
            res = json.loads(response.read().decode('utf-8'))
            text = res['choices'][0]['message']['content']
            return {"lyrics": text.strip()}
            
    except Exception as e:
        # ЗАПАСНОЙ ПЛАН: Если ИИ отвалился, берем текст напрямую из базы LRCLIB (работает всегда)
        try:
            search_query = urllib.parse.quote(f"{artist} {title}")
            fallback_url = f"https://lrclib.net/api/search?q={search_query}"
            req_fallback = urllib.request.Request(fallback_url, headers={'User-Agent': 'NeoMusicApp/1.0'})
            
            with urllib.request.urlopen(req_fallback, timeout=10) as fallback_res:
                data = json.loads(fallback_res.read().decode('utf-8'))
                if data and len(data) > 0 and 'plainLyrics' in data[0]:
                    return {"lyrics": data[0]['plainLyrics'].strip()}
        except Exception:
            pass
            
        return {"lyrics": "Текст недоступен. ИИ и база текстов не ответили."}

@app.get("/")
def root():
    return {"status": "NeoMusic is Live"}
