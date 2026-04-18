import logging
import os
import yt_dlp
import asyncio
import time
import threading
import http.server
import socketserver
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# --- الإعدادات الخاصة ---
TOKEN = '8512467148:AAEWX7qcBNe0_s_JXXXUYlJXX1RcbBOYuOA'
CHANNEL_ID = '@YourChannelUsername'  # استبدله بيوزر قناتك
CHANNEL_URL = 'https://t.me/YourChannelUsername'

# إعداد السجلات
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', 
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# --- وظيفة إرضاء منصة Render (Health Check) ---
def run_health_check():
    """فتح منفذ وهمي لمنع Render من إيقاف البوت"""
    PORT = int(os.environ.get("PORT", 8080))
    handler = http.server.SimpleHTTPRequestHandler
    # السماح بإعادة استخدام المنفذ لتجنب أخطاء التشغيل المتكرر
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("", PORT), handler) as httpd:
        print(f"✅ Health Check يعمل على المنفذ: {PORT}")
        httpd.serve_forever()

# --- وظائف البوت الأساسية ---
async def is_subscribed(user_id, context):
    if not CHANNEL_ID.startswith('@'): return True
    try:
        member = await context.bot.get_chat_member(chat_id=CHANNEL_ID, user_id=user_id)
        return member.status in ['member', 'administrator', 'creator']
    except Exception: return False

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"مرحباً {update.effective_user.first_name}!\nأرسل رابط الفيديو وسأقوم بتحميله.")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    url = update.message.text

    if not await is_subscribed(user_id, context):
        keyboard = [[InlineKeyboardButton("الاشتراك في القناة ✅", url=CHANNEL_URL)]]
        await update.message.reply_text("⚠️ اشترك في القناة أولاً لاستخدام البوت.", reply_markup=InlineKeyboardMarkup(keyboard))
        return

    status_msg = await update.message.reply_text('⏳ جاري المعالجة...')
    file_path = f"video_{user_id}_{int(time.time())}.mp4"

    try:
        ydl_opts = {
            'format': 'best[ext=mp4]/best',
            'outtmpl': file_path,
            'max_filesize': 48 * 1024 * 1024, # 48MB
            'quiet': True
        }
        await asyncio.to_thread(lambda: yt_dlp.YoutubeDL(ydl_opts).download([url]))

        if os.path.exists(file_path):
            await status_msg.edit_text("📤 جاري الرفع...")
            with open(file_path, 'rb') as video:
                await context.bot.send_video(chat_id=update.effective_chat.id, video=video, supports_streaming=True)
            await status_msg.delete()
        else:
            await status_msg.edit_text("❌ لم يتم العثور على الفيديو أو الحجم كبير جداً.")
    except Exception as e:
        logger.error(e)
        await status_msg.edit_text("❌ فشل التحميل.")
    finally:
        if os.path.exists(file_path): os.remove(file_path)

def main():
    # 1. تشغيل الـ Health Check في خلفية الكود (Thread)
    threading.Thread(target=run_health_check, daemon=True).start()

    # 2. تشغيل البوت
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    print("🚀 البوت يعمل الآن...")
    app.run_polling(drop_pending_updates=True
