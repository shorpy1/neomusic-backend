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

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
    prompt = f"Напиши текст песни {artist} - {title}. Отправь ТОЛЬКО текст песни, без лишних слов."
    data = {"contents": [{"parts": [{"text": prompt}]}]}

    try:
        req = urllib.request.Request(
            url, 
            data=json.dumps(data).encode('utf-8'), 
            headers={'Content-Type': 'application/json'}
        )
        with urllib.request.urlopen(req) as response:
            res = json.loads(response.read().decode('utf-8'))
            # Проверяем, есть ли ответ от ИИ
            if 'candidates' in res and res['candidates']:
                text = res['candidates'][0]['content']['parts'][0]['text']
                return JSONResponse(content={"lyrics": text.strip()})
            else:
                return {"lyrics": f"ИИ не выдал результат. Ответ: {json.dumps(res)}"}
                
    except urllib.error.HTTPError as e:
        # Если Google вернул ошибку (например 400 или 403), мы её увидим
        error_msg = e.read().decode('utf-8')
        return {"lyrics": f"Ошибка Google ({e.code}): {error_msg}"}
    except Exception as e:
        return {"lyrics": f"Ошибка сервера: {str(e)}"}

@app.get("/")
def root():
    return {"status": "NeoMusic Server is running!"}
