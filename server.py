import yt_dlp
import urllib.request
import json
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse

app = FastAPI()

# Возвращаемся на SoundCloud, так как YouTube блокирует IP Render'a
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
        print(f"ОШИБКА СТРИМА: {e}")
        return JSONResponse({"error": str(e)}, status_code=500)

@app.get("/api/lyrics")
def get_lyrics(artist: str, title: str):
    # Используем твой 100% рабочий ключ от AIML API
    url = "https://api.aimlapi.com/v1/chat/completions"
    api_key = "5997b8813862455095a9e54bc7ea1c3d"
    
    prompt = f"Напиши только текст песни {artist} - {title}. Без аккордов и твоих комментариев."
    payload = {
        "model": "google/gemma-3-4b-it",
        "messages": [{"role": "user", "content": prompt}]
    }

    try:
        req = urllib.request.Request(
            url, 
            data=json.dumps(payload).encode('utf-8'), 
            headers={
                'Authorization': f'Bearer {api_key}',
                'Content-Type': 'application/json'
            }
        )
        with urllib.request.urlopen(req, timeout=15) as response:
            res = json.loads(response.read().decode('utf-8'))
            text = res['choices'][0]['message']['content']
            return {"lyrics": text.strip()}
    except urllib.error.HTTPError as e:
        err_body = e.read().decode('utf-8')
        print(f"ОШИБКА ИИ: {e.code} - {err_body}")
        return {"lyrics": f"Ошибка сети ({e.code}). Попробуй еще раз."}
    except Exception as e:
        return {"lyrics": f"Текст временно недоступен."}

@app.get("/")
def root():
    return {"status": "NeoMusic Final is Live"}
