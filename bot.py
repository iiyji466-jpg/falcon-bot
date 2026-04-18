import logging
import os
import yt_dlp
import asyncio
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes

# --- الإعدادات ---
TOKEN = '8668387351:AAHhKiD9RmBjfUNSREdu0KnSddcMxFPExBQ'

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- سيرفر Health Check لمنع توقف Render ---
class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/plain')
        self.end_headers()
        self.wfile.write(b"Bot is running alive!")

    def log_message(self, format, *args):
        return  # إخفاء سجلات السيرفر لتبقى الشاشة نظيفة للأخطاء المهمة

def run_health_server():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(("0.0.0.0", port), HealthHandler)
    logger.info(f"Health check server started on port {port}")
    server.serve_forever()

# تشغيل السيرفر في Thread منفصل قبل تشغيل البوت
threading.Thread(target=run_health_server, daemon=True).start()

# --- وظائف البوت ---

def extract_direct_link(url, mode):
    ydl_opts = {
        'format': 'best[ext=mp4]/best' if mode == "video" else 'bestaudio/best',
        'quiet': True,
        'no_warnings': True,
        'nocheckcertificate': True,
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            return info.get('url'), info.get('title', 'video')
    except Exception as e:
        logger.error(f"Error extracting link: {e}")
        return None, None

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🚀 أرسل الرابط، وسأعطيك التحميل فوراً!")

async def handle_msg(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text
    if "http" not in url: return
    
    kb = [[
        InlineKeyboardButton("🎬 فيديو سريع", callback_data=f"v|{url}"),
        InlineKeyboardButton("🎵 صوت MP3", callback_data=f"a|{url}")
    ]]
    await update.message.reply_text("⚡ اختر طريقة التحميل:", reply_markup=InlineKeyboardMarkup(kb))

async def cb_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    data = query.data.split("|")
    mode = "video" if data[0] == "v" else "audio"
    target_url = data[1]

    msg = await query.edit_message_text("⚡ جاري استخراج الرابط المباشر...")

    loop = asyncio.get_event_loop()
    direct_link, title = await loop.run_in_executor(None, extract_direct_link, target_url, mode)

    if direct_link:
        # زر المشاركة ورسالة الشكر
        share_url = f"https://t.me/share/url?url={target_url}&text=شاهد هذا الفيديو!"
        share_kb = InlineKeyboardMarkup([[
            InlineKeyboardButton("📤 مشاركة الملف", url=share_url)
        ]])
        
        thanks_msg = f"✅ {title}\n\nشكراً لاختيارك بوت التحميل الخاص بنا! ❤️"

        try:
            if mode == "video":
                await query.message.reply_video(video=direct_link, caption=thanks_msg, reply_markup=share_kb)
            else:
                await query.message.reply_audio(audio=direct_link, caption=thanks_msg, reply_markup=share_kb)
            await msg.delete()
        except Exception as e:
            await msg.edit_text("❌ عذراً، الملف كبير جداً للإرسال المباشر.")
    else:
        await msg.edit_text("❌ فشل الاستخراج. تأكد من أن الرابط مدعوم.")

def main():
    app = Application.builder().token(TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_msg))
    app.add_handler(CallbackQueryHandler(cb_handler))
    
    logger.info("Bot is starting...")
    app.run_polling(drop_pending_updates=True)

if __name__ == '__main__':
    main()
