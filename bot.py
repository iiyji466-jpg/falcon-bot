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
# ملاحظة: يفضل دائماً وضع التوكن في Environment Variables على Render لحمايته
TOKEN = os.environ.get('BOT_TOKEN', '8668387351:AAHhKiD9RmBjfUNSREdu0KnSddcMxFPExBQ')

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)
executor = ThreadPoolExecutor(max_workers=20)

# --- سيرفر Health Check لضمان استمرار Render ---
def run_health_check():
    PORT = int(os.environ.get("PORT", 8080))
    handler = http.server.SimpleHTTPRequestHandler
    socketserver.TCPServer.allow_reuse_address = True
    try:
        with socketserver.TCPServer(("", PORT), handler) as httpd:
            logger.info(f"Health check server started on port {PORT}")
            httpd.serve_forever()
    except Exception as e:
        logger.error(f"Health Check Error: {e}")

# تشغيل السيرفر في خلفية منفصلة
threading.Thread(target=run_health_check, daemon=True).start()

# --- دالة التحميل ---
def download_content(url, download_path, mode):
    try:
        if mode == "video":
            ydl_opts = {
                'format': 'best[height<=720][ext=mp4]/best[ext=mp4]/best',
                'outtmpl': download_path,
                'noplaylist': True,
                'quiet': True,
                'nocheckcertificate': True,
            }
        else:  # صوت MP3
            ydl_opts = {
                'format': 'bestaudio/best',
                'outtmpl': download_path.replace('.mp4', ''),
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }],
                'quiet': True,
                'nocheckcertificate': True,
            }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        return True
    except Exception as e:
        logger.error(f"Download error: {e}")
        return False

# --- معالجة الرسائل ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("أهلاً بك! أرسل لي رابط الفيديو (يوتيوب، إنستغرام، تيك توك) وسأقوم بتحميله لك.")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text
    if not url.startswith("http"):
        await update.message.reply_text("من فضلك أرسل رابطاً صحيحاً.")
        return

    keyboard = [
        [
            InlineKeyboardButton("فيديو MP4", callback_data=f"video|{url}"),
            InlineKeyboardButton("صوت MP3", callback_data=f"audio|{url}"),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("اختر الصيغة المطلوبة:", reply_markup=reply_markup)

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    data = query.data.split("|")
    mode = data[0]
    url = data[1]
    
    chat_id = query.message.chat_id
    sent_message = await query.edit_message_text("جاري المعالجة... انتظر قليلاً ⏳")

    file_path = f"download_{chat_id}_{int(asyncio.get_event_loop().time())}.mp4"
    if mode == "audio":
        file_path = file_path.replace(".mp4", ".mp3")

    # تنفيذ التحميل في Thread منفصل لعدم تعطيل البوت
    loop = asyncio.get_event_loop()
    success = await loop.run_in_executor(executor, download_content, url, file_path, mode)

    if success and os.path.exists(file_path):
        await query.message.reply_text("تم التحميل بنجاح! جاري الرفع... 📤")
        with open(file_path, 'rb') as f:
            if mode == "video":
                await context.bot.send_video(chat_id=chat_id, video=f)
            else:
                await context.bot.send_audio(chat_id=chat_id, audio=f)
        os.remove(file_path) # حذف الملف بعد الرفع لتوفير المساحة
    else:
        await query.message.reply_text("عذراً، فشل التحميل. تأكد من الرابط أو حاول لاحقاً.")

# --- تشغيل البوت ---
def main():
    # بناء التطبيق
    application = Application.builder().token(TOKEN).build()

    # إضافة الأوامر
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_handler(CallbackQueryHandler(button_callback))

    # تشغيل البوت بنظام Polling
    # ملاحظة: تم إضافة drop_pending_updates لحل مشكلة التعارض عند إعادة التشغيل
    application.run_polling(drop_pending_updates=True)

if __name__ == '__main__':
    main()
