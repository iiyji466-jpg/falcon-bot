import logging
import os
import yt_dlp
import asyncio
import time
import threading
import http.server
import socketserver
from concurrent.futures import ThreadPoolExecutor
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# --- الإعدادات ---
TOKEN = '8668387351:AAHhKiD9RmBjfUNSREdu0KnSddcMxFPExBQ'

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)
executor = ThreadPoolExecutor(max_workers=20)

# --- سيرفر Health Check لضمان استقرار Render ---
def run_health_check():
    PORT = int(os.environ.get("PORT", 8080))
    handler = http.server.SimpleHTTPRequestHandler
    socketserver.TCPServer.allow_reuse_address = True
    try:
        with socketserver.TCPServer(("", PORT), handler) as httpd:
            httpd.serve_forever()
    except Exception as e:
        logger.error(f"Health Check Error: {e}")

# --- دالة التحميل ---
def download_video(url, download_path):
    ydl_opts = {
        'format': 'best[height<=720][ext=mp4]/best[ext=mp4]/best',
        'outtmpl': download_path,
        'noplaylist': True,
        'quiet': True,
        'no_warnings': True,
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'nocheckcertificate': True,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])

# --- أوامر البوت ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🚀 أهلاً بك في بوت بازل للتحميل!\n\nأرسل لي أي رابط فيديو وسأقوم بتحميله لك فوراً.")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text
    if not url.startswith('http'): return

    status_msg = await update.message.reply_text('⏳ جاري التحميل... انتظر قليلاً')
    file_path = f"vid_{update.effective_user.id}_{int(time.time())}.mp4"

    try:
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(executor, download_video, url, file_path)

        if os.path.exists(file_path):
            await status_msg.edit_text("📤 جاري إرسال الفيديو...")
            
            with open(file_path, 'rb') as v:
                # هنا كان الخطأ (تم إغلاق القوس بشكل صحيح الآن)
                await context.bot.send_video(
                    chat_id=update.effective_chat.id,
                    video=v,
                    caption="✅ تم تحميل المقطع بنجاح!\n\nشكراً لاستخدامك بوت بازل، نتمنى لك مشاهدة ممتعة 🌹",
                    supports_streaming=True
                )
            await status_msg.delete()
        else:
            await status_msg.edit_text("❌ لم أتمكن من العثور على الفيديو.")

    except Exception as e:
        logger.error(f"Error: {e}")
        await status_msg.edit_text("❌ فشل التحميل. قد يكون الرابط خاصاً أو محمياً.")
    
    finally:
        if os.path.exists(file_path):
            try: os.remove(file_path)
            except: pass

def main():
    # تشغيل الهيلث تشيك في خلفية البرنامج
    threading.Thread(target=run_health_check, daemon=True).start()
    
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    logger.info("Bot is running...")
    app.run_polling(drop_pending_updates=True)

if __name__ == '__main__':
    main()
