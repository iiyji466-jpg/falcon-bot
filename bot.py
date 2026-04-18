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

# --- الإعدادات (تأكد من تغييرها) ---
TOKEN = '8512467148:AAEWX7qcBNe0_s_JXXXUYlJXX1RcbBOYuOA'
CHANNEL_ID = ''  # اتركها فارغة إذا لم تكن تملك قناة حالياً
CHANNEL_URL = 'https://t.me/YourChannelUsername'
# --------------------

logging.basicConfig(level=logging.INFO)

def run_health_check():
    PORT = int(os.environ.get("PORT", 8080))
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("", PORT), http.server.SimpleHTTPRequestHandler) as httpd:
        httpd.serve_forever()

async def is_subscribed(user_id, context):
    if not CHANNEL_ID or not CHANNEL_ID.startswith('@'): return True
    try:
        member = await context.bot.get_chat_member(chat_id=CHANNEL_ID, user_id=user_id)
        return member.status in ['member', 'administrator', 'creator']
    except: return False

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"مرحباً بك! أنا أعمل الآن ✅\nأرسل أي رابط فيديو وسأحمله لك.")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    url = update.message.text
    if not url.startswith('http'): return

    if not await is_subscribed(user_id, context):
        keyboard = [[InlineKeyboardButton("الاشتراك في القناة ✅", url=CHANNEL_URL)]]
        await update.message.reply_text("⚠️ اشترك أولاً ثم أرسل الرابط مجدداً.", reply_markup=InlineKeyboardMarkup(keyboard))
        return

    status_msg = await update.message.reply_text('⏳ جاري جلب الفيديو...')
    file_path = f"vid_{int(time.time())}.mp4"

    try:
        ydl_opts = {
            'format': 'best',
            'outtmpl': file_path,
            'quiet': True,
            'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36'
        }
        await asyncio.to_thread(lambda: yt_dlp.YoutubeDL(ydl_opts).download([url]))

        if os.path.exists(file_path):
            share_url = f"https://t.me/share/url?url={urllib.parse.quote('جرب هذا البوت الرهيب لتحميل الفيديوهات! 📥')}"
            keyboard = [[InlineKeyboardButton("مشاركة البوت 🚀", url=share_url)]]
            
            with open(file_path, 'rb') as video:
                await context.bot.send_video(chat_id=update.effective_chat.id, video=video, caption="✅ تم التحميل بنجاح!", reply_markup=InlineKeyboardMarkup(keyboard))
            await status_msg.delete()
        else:
            await status_msg.edit_text("❌ لم أتمكن من تحميل الفيديو. تأكد أن الحساب ليس خاصاً.")
    except Exception as e:
        await status_msg.edit_text("❌ فشل التحميل. قد يكون الرابط غير مدعوم حالياً.")
    finally:
        if os.path.exists(file_path): os.remove(file_path)

def main():
    threading.Thread(target=run_health_check, daemon=True).start()
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.run_polling(drop_pending_updates=True)

if __name__ == '__main__':
    main()
