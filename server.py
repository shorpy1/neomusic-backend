import yt_dlp
import urllib.request
import json
import os
from fastapi import FastAPI
from fastapi.responses import JSONResponse

app = FastAPI()

@app.get("/api/stream")
def get_stream(q: str):
    ydl_opts = {'format': 'bestaudio/best', 'noplaylist': True, 'quiet': True}
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(f"scsearch1:{q}", download=False)
            return {"stream_url": info['entries'][0].get('url')}
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)

@app.get("/api/lyrics")
def get_lyrics(artist: str, title: str):
    # .strip() убирает случайные пробелы или переносы строк в ключе
    api_key = os.environ.get("GEMINI_API_KEY", "").strip()
    
    if not api_key:
        return {"lyrics": "Ошибка: Ключ API не настроен в Render (GEMINI_API_KEY)"}

    # Самый стабильный URL для ключей из AI Studio
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
    
    prompt = f"Напиши текст песни {artist} - {title}. Отправь ТОЛЬКО текст песни, без аккордов и комментариев."
    payload = {
        "contents": [{
            "parts": [{
                "text": prompt
            }]
        }]
    }
    
    try:
        data = json.dumps(payload).encode('utf-8')
        req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'})
        
        with urllib.request.urlopen(req, timeout=10) as response:
            res_data = json.loads(response.read().decode('utf-8'))
            
            # Проверяем структуру ответа Gemini
            if 'candidates' in res_data and res_data['candidates']:
                lyrics = res_data['candidates'][0]['content']['parts'][0]['text']
                return {"lyrics": lyrics.strip()}
            else:
                return {"lyrics": "ИИ не смог сгенерировать текст для этого трека."}
                
    except urllib.error.HTTPError as e:
        error_content = e.read().decode('utf-8')
        print(f"!!! ОШИБКА GOOGLE: {error_content}")
        return {"lyrics": f"Ошибка Google: {error_content}"}
    except Exception as e:
        print(f"!!! ОШИБКА СЕРВЕРА: {str(e)}")
        return {"lyrics": f"Ошибка сервера: {str(e)}"}

@app.get("/")
def root():
    return {"status": "NeoMusic Server is Live"}
