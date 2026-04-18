import logging
import os
import yt_dlp
import asyncio
import threading
from concurrent.futures import ThreadPoolExecutor
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
from http.server import SimpleHTTPRequestHandler
import socketserver

# --- الإعدادات ---
TOKEN = '8668387351:AAHhKiD9RmBjfUNSREdu0KnSddcMxFPExBQ'

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

executor = ThreadPoolExecutor(max_workers=20)
url_storage = {}

# --- سيرفر لمنع توقف الخدمة على Render ---
def run_health_server():
    port = int(os.environ.get("PORT", 8080))
    class HealthHandler(SimpleHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"Bot is Active")
    
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("", port), HealthHandler) as httpd:
        httpd.serve_forever()

threading.Thread(target=run_health_server, daemon=True).start()

# --- محرك التحميل المتطور ---
def download_engine(url, mode):
    # إعدادات لتجاوز حظر يوتيوب وسرعة المعالجة
    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'nocheckcertificate': True,
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36',
    }

    if mode == "video":
        ydl_opts.update({
            'format': 'best[height<=720][ext=mp4]/best',
            'outtmpl': 'downloads/%(id)s.%(ext)s'
        })
    else:
        ydl_opts.update({
            'format': 'bestaudio/best',
            'outtmpl': 'downloads/%(id)s.%(ext)s',
            'postprocessors': [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3', 'preferredquality': '192'}]
        })

    try:
        if not os.path.exists('downloads'): os.makedirs('downloads')
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            return ydl.prepare_filename(info).replace(".unknown_video", ".mp4") if mode == "video" else ydl.prepare_filename(info).rsplit('.', 1)[0] + ".mp3"
    except Exception as e:
        logger.error(f"Download Error: {e}")
        return None

# --- معالجة الأوامر ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🚀 أرسل رابط الفيديو الآن للتحميل السريع!")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text
    if "http" not in url: return
    
    msg_id = str(update.message.message_id)
    url_storage[msg_id] = url
    
    keyboard = [[
        InlineKeyboardButton("🎬 فيديو MP4", callback_data=f"v_{msg_id}"),
        InlineKeyboardButton("🎵 صوت MP3", callback_data=f"a_{msg_id}")
    ]]
    await update.message.reply_text("⚡ اختر ما تريد تحميله:", reply_markup=InlineKeyboardMarkup(keyboard))

async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    prefix, msg_id = query.data.split("_")
    url = url_storage.get(msg_id)
    if not url: return

    mode = "video" if prefix == "v" else "audio"
    status = await query.edit_message_text("🔄 جاري التحميل... (عادةً أقل من 10 ثوانٍ)")

    loop = asyncio.get_event_loop()
    path = await loop.run_in_executor(executor, download_engine, url, mode)

    if path and os.path.exists(path):
        await status.edit_text("📤 جاري الرفع...")
        with open(path, 'rb') as f:
            if mode == "video":
                await context.bot.send_video(chat_id=query.message.chat_id, video=f, supports_streaming=True)
            else:
                await context.bot.send_audio(chat_id=query.message.chat_id, audio=f)
        os.remove(path)
    else:
        await status.edit_text("❌ فشل التحميل، تأكد من صحة الرابط.")

# --- التشغيل الأساسي ---
def main():
    # استخدام drop_pending_updates هو الحل الجذري لمشكلة Conflict
    app = Application.builder().token(TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(CallbackQueryHandler(callback_handler))
    
    logger.info("Bot is running...")
    app.run_polling(drop_pending_updates=True)

if __name__ == '__main__':
    main()
