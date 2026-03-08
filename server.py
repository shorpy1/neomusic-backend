import yt_dlp
from fastapi import FastAPI, HTTPException

app = FastAPI(title="NeoMusic Backend")

stream_cache = {}

YDL_OPTIONS = {
    'format': 'bestaudio/best',
    'noplaylist': True,
    'quiet': True,
    'skip_download': True,
    'extract_flat': False
}

@app.get("/api/stream")
def get_stream(q: str):
    if q in stream_cache:
        print(f"⚡️ Отдаю из кэша: {q}")
        return {"stream_url": stream_cache[q]}

    # ХИТРОСТЬ: Ищем в SoundCloud (scsearch1:) вместо YouTube.
    # SoundCloud не банит IP-адреса серверов Render!
    search_query = f"scsearch1:{q}"
    print(f"🔍 Ищу: {search_query}")

    try:
        with yt_dlp.YoutubeDL(YDL_OPTIONS) as ydl:
            info = ydl.extract_info(search_query, download=False)
            
        if not info or 'entries' not in info or not info['entries']:
            print(f"❌ Ничего не найдено для: {q}")
            raise HTTPException(status_code=404, detail="Песня не найдена")
            
        track = info['entries'][0]
        
        # SoundCloud сразу отдает прямую аудио-ссылку
        audio_url = track.get('url')
            
        if not audio_url:
            print(f"❌ Нет ссылки для: {q}")
            raise HTTPException(status_code=404, detail="Нет ссылки")
            
        stream_cache[q] = audio_url
        print(f"✅ Успех: {q}")
        return {"stream_url": audio_url}
        
    except Exception as e:
        print(f"❌ Ошибка yt-dlp: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Исправляем ошибку 404 при простом переходе по ссылке
@app.get("/")
def root():
    return {"status": "NeoMusic Server is running on SoundCloud bypass! 🎵"}
