import logging
import os
import yt_dlp
import asyncio
import time
import threading
import http.server
import socketserver
import urllib.parse
from concurrent.futures import ThreadPoolExecutor
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# --- الإعدادات الأساسية ---
TOKEN = '8668387351:AAHhKiD9RmBjfUNSREdu0KnSddcMxFPExBQ'
CHANNEL_ID = ''  # مثال: '@MyChannel'
CHANNEL_URL = 'https://t.me/YourChannel'

# إعداد السجلات
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', 
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# منشئ المهام لتسريع العمليات
executor = ThreadPoolExecutor(max_workers=10)

# --- سيرفر Health Check ---
def run_health_check():
    PORT = int(os.environ.get("PORT", 8080))
    handler = http.server.SimpleHTTPRequestHandler
    socketserver.TCPServer.allow_reuse_address = True
    try:
        with socketserver.TCPServer(("", PORT), handler) as httpd:
            logger.info(f"Health Check active on port {PORT}")
            httpd.serve_forever()
    except Exception as e:
        logger.error(f"Health Check Error: {e}")

# --- التحقق من الاشتراك ---
async def is_subscribed(user_id, context):
    if not CHANNEL_ID: return True
    try:
        member = await context.bot.get_chat_member(chat_id=CHANNEL_ID, user_id=user_id)
        return member.status in ['member', 'administrator', 'creator']
    except:
        return False

# --- معالج التحميل الرئيسي ---
def download_video(url, download_path):
    ydl_opts = {
        # جودة الفيديو: الأفضل (MP4) أو دمج أفضل فيديو وصوت
        'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
        'outtmpl': download_path,
        'quiet': True,
        'no_warnings': True,
        'nocheckcertificate': True,
        'ignoreerrors': False,
        'add_header': [
            'User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        ],
        # لضمان التحميل من المواقع التي تتطلب ملفات تعريف ارتباط (اختياري)
        'cookiefile': None, 
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        return ydl.prepare_filename(info)

# --- أوامر البوت ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 أهلاً بك في بوت التحميل العالمي!\n\n"
        "🚀 **ماذا يمكنني أن أفعل؟**\n"
        "أرسل لي أي رابط من (YouTube, TikTok, Instagram, Twitter, Facebook) "
        "أو أي موقع تواصل آخر وسأقوم بتحميله لك فوراً بأعلى جودة."
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    url = update.message.text

    if not url.startswith('http'):
        return

    # فحص الاشتراك الإجباري
    if not await is_subscribed(user_id, context):
        keyboard = [[InlineKeyboardButton("اضغط هنا للاشتراك ✅", url=CHANNEL_URL)]]
        await update.message.reply_text(
            "⚠️ عذراً! يجب عليك الاشتراك في القناة أولاً لاستخدام البوت.",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return

    status_msg = await update.message.reply_text('⏳ جاري جلب البيانات ومعالجة الرابط...')
    
    # اسم ملف فريد لتجنب التداخل
    file_id = f"{user_id}_{int(time.time())}"
    file_path = f"video_{file_id}.mp4"

    try:
        # تشغيل التحميل في Thread منفصل لضمان سرعة الاستجابة
        loop = asyncio.get_event_loop()
        final_path = await loop.run_in_executor(executor, download_video, url, file_path)

        if os.path.exists(final_path):
            await status_msg.edit_text("📤 جاري رفع الفيديو... انتظر قليلاً")
            
            with open(final_path, 'rb') as video_file:
                await context.bot.send_video(
                    chat_id=update.effective_chat.id,
                    video=video_file,
                    caption=f"✅ تم التحميل بنجاح!\n\n🔗 الرابط: {url}",
                    supports_streaming=True
                )
            await status_msg.delete()
        else:
            raise FileNotFoundError

    except Exception as e:
        logger.error(f"Download Error: {e}")
        await status_msg.edit_text("❌ فشل التحميل. قد يكون الرابط غير مدعوم، خاص، أو حجمه كبير جداً.")
    
    finally:
        # تنظيف الملفات لضمان عدم امتلاء القرص الصلب
        for file in os.listdir():
            if file.startswith(f"video_{file_id}"):
                try: os.remove(file)
                except: pass

def main():
    # تشغيل سيرفر الـ Health Check
    threading.Thread(target=run_health_check, daemon=True).start()

    # إعداد تطبيق التيليجرام
    app = Application.builder().token(TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    print("--- البوت يعمل الآن بنجاح ---")
    app.run_polling(drop_pending_updates=True)

if __name__ == '__main__':
    main()
