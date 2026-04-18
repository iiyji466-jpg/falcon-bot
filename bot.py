import logging
import os
import yt_dlp
import asyncio
import time
import threading
import http.server
import socketserver
import urllib.parse
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# --- الإعدادات الأساسية ---
TOKEN = '8512467148:AAEWX7qcBNe0_s_JXXXUYlJXX1RcbBOYuOA'
CHANNEL_ID = ''  # ضع معرف قناتك هنا مثل '@mychannel' أو اتركه فارغاً
CHANNEL_URL = 'https://t.me/YourChannelUsername'

# إعداد السجلات (Logs)
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', 
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# --- ميزة Health Check لمنصات الاستضافة مثل Render ---
def run_health_check():
    PORT = int(os.environ.get("PORT", 8080))
    handler = http.server.SimpleHTTPRequestHandler
    socketserver.TCPServer.allow_reuse_address = True
    try:
        with socketserver.TCPServer(("", PORT), handler) as httpd:
            logger.info(f"Health check server started on port {PORT}")
            httpd.serve_forever()
    except Exception as e:
        logger.error(f"Health check failed: {e}")

# --- التحقق من الاشتراك الإجباري ---
async def is_subscribed(user_id, context):
    if not CHANNEL_ID or not CHANNEL_ID.startswith('@'):
        return True
    try:
        member = await context.bot.get_chat_member(chat_id=CHANNEL_ID, user_id=user_id)
        return member.status in ['member', 'administrator', 'creator']
    except Exception:
        return False

# --- أوامر البوت ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_name = update.effective_user.first_name
    await update.message.reply_text(
        f"مرحباً {user_name}! 🤖\n\n"
        "أنا بوت تحميل سريع وقوي. أرسل لي أي رابط من:\n"
        "• Instagram 📸\n• TikTok 🎵\n• YouTube 🎥\n"
        "وسأقوم بإرسال الفيديو لك فوراً."
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    url = update.message.text
    
    if not url.startswith('http'):
        return

    # فحص الاشتراك
    if not await is_subscribed(user_id, context):
        keyboard = [[InlineKeyboardButton("الاشتراك في القناة ✅", url=CHANNEL_URL)]]
        await update.message.reply_text(
            "⚠️ عذراً! يجب عليك الاشتراك في القناة أولاً لتتمكن من استخدام البوت.",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return

    status_msg = await update.message.reply_text('🚀 جاري المعالجة... انتظر قليلاً')
    file_path = f"vid_{user_id}_{int(time.time())}.mp4"

    # إعدادات yt-dlp الاحترافية
    ydl_opts = {
        'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
        'outtmpl': file_path,
        'quiet': True,
        'no_warnings': True,
        'nocheckcertificate': True,
        'ignoreerrors': False,
        'logtostderr': False,
        'no_color': True,
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }

    try:
        # تنفيذ التحميل
        await asyncio.to_thread(lambda: yt_dlp.YoutubeDL(ydl_opts).download([url]))

        if os.path.exists(file_path):
            await status_msg.edit_text("📤 جاري الرفع إلى تيليجرام...")
            
            # زر المشاركة
            share_text = urllib.parse.quote(f"حمل فيديوهاتك بسهولة عبر هذا البوت! 🔥")
            share_url = f"https://t.me/share/url?url={share_text}"
            keyboard = [[InlineKeyboardButton("مشاركة البوت 🚀", url=share_url)]]
            
            with open(file_path, 'rb') as video:
                await context.bot.send_video(
                    chat_id=update.effective_chat.id,
                    video=video,
                    caption=f"✅ تم التحميل بنجاح!\n\nبواسطة: @{context.bot.username}",
                    supports_streaming=True,
                    reply_markup=InlineKeyboardMarkup(keyboard)
                )
            await status_msg.delete()
        else:
            await status_msg.edit_text("❌ عذراً، لم أتمكن من العثور على الفيديو. قد يكون الرابط خاصاً أو محمي.")

    except Exception as e:
        logger.error(f"Error: {e}")
        await status_msg.edit_text("❌ فشل التحميل! تأكد من صحة الرابط أو حاول لاحقاً.")
    
    finally:
        # تنظيف الملفات دائماً
        if os.path.exists(file_path):
            os.remove(file_path)

def main():
    # بدء تشغيل سيرفر الـ Health Check في خلفية البرنامج
    threading.Thread(target=run_health_check, daemon=True).start()

    # إنشاء التطبيق
    app = Application.builder().token(TOKEN).build()
    
    # الروابط والمستقبلات
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    logger.info("Bot is running...")
    app.run_polling(drop_pending_updates=True)

if __name__ == '__main__':
    main()
