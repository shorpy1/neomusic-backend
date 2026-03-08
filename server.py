import yt_dlp
from fastapi import FastAPI, HTTPException

app = FastAPI(title="NeoMusic Backend")

stream_cache = {}

# Максимально надежные настройки
YDL_OPTIONS = {
    'format': 'bestaudio/best',
    'noplaylist': True,
    'quiet': True,
    'skip_download': True,
    'extract_flat': False,
    'default_search': 'ytsearch' # <--- ВОТ ОНО! Указываем явно, что мы ИЩЕМ, а не переходим по ссылке
}

@app.get("/api/stream")
def get_stream(q: str):
    if q in stream_cache:
        print(f"⚡️ Отдаю из кэша: {q}")
        return {"stream_url": stream_cache[q]}

    # Теперь мы просто передаем название песни, никаких префиксов!
    search_query = f"{q} official audio"
    print(f"🔍 Ищу: {search_query}")

    try:
        with yt_dlp.YoutubeDL(YDL_OPTIONS) as ydl:
            # Парсим Ютуб
            info = ydl.extract_info(search_query, download=False)
            
        if not info or 'entries' not in info or not info['entries']:
            print(f"❌ Ничего не найдено для: {q}")
            raise HTTPException(status_code=404, detail="Песня не найдена")
            
        track = info['entries'][0]
        audio_url = None
        
        # Ищем чистый аудиопоток
        for f in track.get('formats', []):
            if f.get('acodec') != 'none' and f.get('vcodec') == 'none':
                audio_url = f.get('url')
                break
        
        # Запасной вариант, если чистого аудио нет
        if not audio_url:
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
