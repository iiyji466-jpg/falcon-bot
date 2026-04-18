import logging
import os
import yt_dlp
import asyncio
import threading
import http.server
import socketserver
from concurrent.futures import ThreadPoolExecutor
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes

# --- الإعدادات ---
TOKEN = '8668387351:AAHhKiD9RmBjfUNSREdu0KnSddcMxFPExBQ'

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)
executor = ThreadPoolExecutor(max_workers=10)
url_cache = {}

# --- سيرفر Health Check ---
def run_health_check():
    PORT = int(os.environ.get("PORT", 8080))
    class HealthHandler(http.server.SimpleHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"Bot is Live!")
    socketserver.TCPServer.allow_reuse_address = True
    try:
        with socketserver.TCPServer(("", PORT), HealthHandler) as httpd:
            httpd.serve_forever()
    except Exception as e:
        logger.error(f"Health Check Error: {e}")

threading.Thread(target=run_health_check, daemon=True).start()

# --- دالة التحميل المصححة ---
def download_content(url, file_path, mode):
    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'nocheckcertificate': True,
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
        'geo_bypass': True,
    }

    if mode == "video":
        ydl_opts.update({'format': 'best[height<=720][ext=mp4]/best', 'outtmpl': file_path})
    else:
        ydl_opts.update({
            'format': 'bestaudio/best',
            'outtmpl': file_path.replace('.mp3', ''),
            'postprocessors': [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3', 'preferredquality': '192'}],
        })

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        return True
    except Exception as e:
        logger.error(f"Download Error: {e}")
        return False

# --- المعالجات ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("أرسل رابط الفيديو للبدء.")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text
    if not url.startswith("http"): return
    link_id = str(update.message.message_id)
    url_cache[link_id] = url
    keyboard = [[InlineKeyboardButton("فيديو MP4", callback_data=f"v_{link_id}"),
                 InlineKeyboardButton("صوت MP3", callback_data=f"a_{link_id}")]]
    await update.message.reply_text("اختر الصيغة:", reply_markup=InlineKeyboardMarkup(keyboard))

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    prefix, link_id = query.data.split("_")
    url = url_cache.get(link_id)
    if not url: return
    
    mode = "video" if prefix == "v" else "audio"
    ext = "mp4" if mode == "video" else "mp3"
    file_path = f"file_{link_id}.{ext}"
    
    await query.edit_message_text("⏳ جاري التحميل...")
    loop = asyncio.get_event_loop()
    success = await loop.run_in_executor(executor, download_content, url, file_path, mode)

    if success and os.path.exists(file_path):
        with open(file_path, 'rb') as f:
            if mode == "video":
                await context.bot.send_video(chat_id=query.message.chat_id, video=f)
            else:
                await context.bot.send_audio(chat_id=query.message.chat_id, audio=f)
        os.remove(file_path)
    else:
        await query.message.reply_text("❌ فشل التحميل.")

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
