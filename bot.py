import logging
import os
import yt_dlp
import asyncio
from threading import Thread
from flask import Flask
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

# --- 1. سيرفر Flask (إلزامي لمنصة Render) ---
server = Flask(__name__)

@server.route('/')
def home():
    return "Bot is Active!"

def run_flask():
    # Render يمرر بورت عشوائي، يجب استخدامه
    port = int(os.environ.get("PORT", 8080))
    server.run(host='0.0.0.0', port=port)

# --- 2. إعدادات البوت ---
TOKEN = '8668387351:AAHhKiD9RmBjfUNSREdu0KnSddcMxFPExBQ'

logging.basicConfig(level=logging.INFO)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 أهلاً باسل! أرسل رابط الفيديو للتحميل.")

async def download(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text
    if not url.startswith("http"): return
    
    msg = await update.message.reply_text("⏳ جاري التحميل...")
    file_path = f"video_{update.message.message_id}.mp4"
    
    ydl_opts = {
        'format': 'best',
        'outtmpl': file_path,
        'quiet': True,
        'nocheckcertificate': True
    }
    
    try:
        # التحميل بدون تعطيل البوت
        await asyncio.to_thread(lambda: yt_dlp.YoutubeDL(ydl_opts).download([url]))
        
        with open(file_path, 'rb') as f:
            await context.bot.send_video(chat_id=update.effective_chat.id, video=f)
        os.remove(file_path)
        await msg.delete()
    except Exception as e:
        await msg.edit_text(f"❌ خطأ: {str(e)[:100]}")

if __name__ == '__main__':
    # تشغيل سيرفر الويب في الخلفية
    Thread(target=run_flask, daemon=True).start()

    # تشغيل البوت بنظام v20.x
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, download))
    
    print("Bot is starting...")
    app.run_polling(drop_pending_updates=True)
