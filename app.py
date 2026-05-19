import os
import logging
from urllib.parse import urlparse
import requests
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext
from telegram.request import HTTPXRequest

# -------------------- НАСТРОЙКИ --------------------
TOKEN = os.environ.get("TELEGRAM_TOKEN", "8348485770:AAEQafsu09GUUU09qMwXoNVsFUksbyzs6i0")
API_URL = os.environ.get("API_URL", "https://youtube-download-api-render.onrender.com")
ADMIN_ID = int(os.environ.get("ADMIN_ID", "7052350977"))

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

def is_valid_url(url: str) -> bool:
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except:
        return False

def detect_platform(url: str) -> str:
    if "youtube.com" in url or "youtu.be" in url:
        return "youtube"
    return "other"

def get_youtube_stream(url: str) -> str:
    try:
        resp = requests.post(
            f"{API_URL}/stream-url",
            json={"url": url},
            headers={"Content-Type": "application/json"},
            timeout=60
        )
        data = resp.json()
        return data.get("stream_url")
    except Exception as e:
        logger.error(f"YouTube stream error: {e}")
        return None

def get_direct_link(url: str) -> str:
    try:
        resp = requests.get(
            f"{API_URL}/dl",
            params={"url": url},
            allow_redirects=False,
            timeout=60
        )
        if resp.status_code == 302:
            return resp.headers.get("Location")
        return None
    except Exception as e:
        logger.error(f"Cobalt redirect error: {e}")
        return None

def download_video_file(url: str) -> bytes:
    try:
        resp = requests.post(
            f"{API_URL}/download",
            json={"url": url},
            headers={"Content-Type": "application/json"},
            timeout=300
        )
        if resp.status_code == 200:
            return resp.content
        return None
    except Exception as e:
        logger.error(f"Download file error: {e}")
        return None

async def start(update: Update, context: CallbackContext) -> None:
    await update.message.reply_text(
        "🎬 *Video Downloader Bot*\n\n"
        "Отправь мне ссылку на видео, и я скачаю его!\n\n"
        "📹 *Поддерживаю:*\n"
        "• YouTube (файл + стрим)\n"
        "• VK, Rutube, Pinterest, Instagram\n"
        "• TikTok, Twitter/X, Reddit\n"
        "• Facebook, Vimeo, Twitch и другие",
        parse_mode="Markdown"
    )

async def status_cmd(update: Update, context: CallbackContext) -> None:
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("⛔ Только для админа.")
        return
    try:
        resp = requests.get(f"{API_URL}/health", timeout=10)
        if resp.ok:
            await update.message.reply_text("✅ API сервер работает.")
        else:
            await update.message.reply_text("⚠️ API сервер отвечает с ошибкой.")
    except:
        await update.message.reply_text("❌ API сервер недоступен!")

async def handle_message(update: Update, context: CallbackContext) -> None:
    url = update.message.text.strip()
    if not is_valid_url(url):
        await update.message.reply_text("❌ Отправь корректную ссылку.")
        return

    platform = detect_platform(url)
    status_msg = await update.message.reply_text("⏳ Обрабатываю...")

    try:
        if platform == "youtube":
            await status_msg.edit_text("🎬 YouTube: скачиваю видео...")
            video_data = download_video_file(url)
            if video_data and len(video_data) < 50 * 1024 * 1024:
                await status_msg.edit_text("📤 Отправляю видео...")
                with open("/tmp/video.mp4", "wb") as f:
                    f.write(video_data)
                await update.message.reply_video(
                    video=open("/tmp/video.mp4", "rb"),
                    caption="✅ Готово!"
                )
                await status_msg.delete()
            else:
                await status_msg.edit_text("📡 Получаю ссылку на стрим...")
                stream_url = get_youtube_stream(url)
                if stream_url:
                    await status_msg.edit_text(
                        f"✅ [Открыть видео]({stream_url})",
                        parse_mode="Markdown",
                        disable_web_page_preview=False
                    )
                else:
                    await status_msg.edit_text("❌ Не удалось получить видео.")
        else:
            await status_msg.edit_text("🔗 Получаю ссылку...")
            direct_link = get_direct_link(url)
            if direct_link:
                await status_msg.edit_text(
                    f"✅ [Скачать файл]({direct_link})",
                    parse_mode="Markdown",
                    disable_web_page_preview=True
                )
            else:
                await status_msg.edit_text("❌ Не удалось получить файл.")
    except Exception as e:
        await status_msg.edit_text(f"❌ Ошибка: {str(e)[:100]}")

def main():
    # Используем свой request с увеличенными таймаутами
    request = HTTPXRequest(connect_timeout=30, read_timeout=60, write_timeout=30)
    app = Application.builder().token(TOKEN).request(request).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("status", status_cmd))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    logger.info("Bot started...")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
