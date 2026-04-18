import logging
import os
import yt_dlp
import asyncio
from threading import Thread
from flask import Flask
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

# --- 1. سيرفر الويب (ضروري جداً لـ Render) ---
server = Flask(__name__)

@server.route('/')
def home():
    return "Bot is Live!"

def run_web():
    # Render يمرر المنفذ عبر متغير PORT
    port = int(os.environ.get("PORT", 8080))
    server.run(host='0.0.0.0', port=port)

# --- 2. إعدادات التحميل ---
def download_video(url, out_name):
    ydl_opts = {
        'format': 'best',
        'outtmpl': out_name,
        'quiet': True,
        'no_warnings': True,
        'nocheckcertificate': True,
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])

# --- 3. معالجات الرسائل ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 أهلاً باسل! البوت يعمل الآن بقوة.\nأرسل لي أي رابط فيديو وسأقوم بتحميله.")

async def handle_msg(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text
    if not url.startswith("http"): return

    status = await update.message.reply_text("⏳ جاري التحميل... يرجى الانتظار.")
    file_name = f"video_{update.message.message_id}.mp4"

    try:
        # تشغيل التحميل في Thread منفصل لعدم تجميد البوت
        await asyncio.to_thread(download_video, url, file_name)

        if os.path.exists(file_name):
            with open(file_name, 'rb') as f:
                await context.bot.send_video(chat_id=update.effective_chat.id, video=f, caption="تم التحميل بنجاح ✅")
            os.remove(file_name)
            await status.delete()
        else:
            await status.edit_text("❌ لم أتمكن من تحميل الفيديو. تأكد من أن الرابط عام.")
    except Exception as e:
        logging.error(f"Error: {e}")
        await status.edit_text("❌ حدث خطأ غير متوقع أثناء التحميل.")

# --- 4. تشغيل البوت ---
if __name__ == '__main__':
    # تشغيل سيرفر الويب في الخلفية
    Thread(target=run_web, daemon=True).start()

    # استخدام التوكن الخاص بك
    TOKEN = '8668387351:AAHhKiD9RmBjfUNSREdu0KnSddcMxFPExBQ'
    
    # بناء التطبيق بنظام v20.x
    app = ApplicationBuilder().token(TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_msg))
    
    logging.info("Starting Polling...")
    app.run_polling(drop_pending_updates=True)
