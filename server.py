import yt_dlp
from fastapi import FastAPI, HTTPException
import uvicorn

app = FastAPI(title="NeoMusic Backend")

# Кэш в оперативной памяти. Хранит готовые ссылки, чтобы не парсить Ютуб дважды.
# Прямые ссылки Ютуба живут около 4-6 часов, для нас этого более чем достаточно.
stream_cache = {}

# Максимально агрессивные и быстрые настройки для yt-dlp
YDL_OPTIONS = {
    'format': 'bestaudio/best', # Берем только лучший звук
    'noplaylist': True,
    'quiet': True,
    'skip_download': True,      # Ничего не скачиваем на диск, только берем ссылку
    'extract_flat': False,
    'extractor_args': {
        'youtube': {'player_client': ['android', 'ios']} # Маскируемся под мобильный телефон
    }
}

@app.get("/api/stream")
def get_stream(q: str):
    # 1. Проверяем, есть ли уже эта песня в кэше
    if q in stream_cache:
        print(f"⚡️ Отдаю из кэша: {q}")
        return {"stream_url": stream_cache[q]}

    # 2. Ищем ТОЛЬКО в YouTube Music (ytmsearch1:) чистый звук
    search_query = f"ytmsearch1:{q} official audio"

    try:
        with yt_dlp.YoutubeDL(YDL_OPTIONS) as ydl:
            info = ydl.extract_info(search_query, download=False)
            
        if not info or 'entries' not in info or not info['entries']:
            raise HTTPException(status_code=404, detail="Песня не найдена")
            
        track = info['entries'][0]
        
        # 3. Ищем поток, где есть только аудио (без видео), чтобы экономить интернет
        audio_url = None
        for f in track.get('formats', []):
            if f.get('acodec') != 'none' and f.get('vcodec') == 'none':
                audio_url = f.get('url')
                break
        
        # Если чистого аудио нет, берем дефолтную ссылку
        if not audio_url:
            audio_url = track.get('url')
            
        if not audio_url:
            raise HTTPException(status_code=404, detail="Не удалось достать ссылку")
            
        # 4. Сохраняем в кэш и отдаем телефону
        stream_cache[q] = audio_url
        print(f"✅ Успешно спарсил: {q}")
        return {"stream_url": audio_url}
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
def root():
    return {"status": "NeoMusic Server is running fast and stealthy! 🚀"}