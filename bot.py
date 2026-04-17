
import os
import asyncio
from threading import Thread
from flask import Flask
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
import yt_dlp

# --- جزء Flask للبقاء حياً ---
app = Flask('')

@app.route('/')
def home():
    return "Bot is Online and Alive!"

def run():
    # Render يستخدم المنفذ 8080 تلقائياً
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run)
    t.daemon = True
    t.start()

# --- إعدادات البوت والتحميل ---

# ⚠️ ضع التوكن الجديد الخاص بك هنا بين العلامتين
TOKEN = '8668387351:AAHhKiD9RmBjfUNSREdu0KnSddcMxFPExBQ' 

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("أهلاً بك! أرسل لي رابط فيديو من يوتيوب أو تيك توك وسأقوم بتحميله لك.")

async def download_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text
    if not url.startswith("http"):
        return

    status_message = await update.message.reply_text("⏳ جاري معالجة الرابط والتحميل...")

    ydl_opts = {
        'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
        'outtmpl': 'video.%(ext)s',
        'quiet': True,
        'no_warnings': True,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            
            await update.message.reply_video(video=open(filename, 'rb'))
            os.remove(filename) # مسح الفيديو بعد الإرسال لتوفير المساحة
            await status_message.delete()
            
    except Exception as e:
        await update.message.reply_text(f"❌ حدث خطأ أثناء التحميل: {str(e)}")

# --- تشغيل كل شيء ---

def main():
    # 1. تشغيل سيرفر الويب
    keep_alive()
    print("Web server started.")

    # 2. تشغيل محرك البوت
    application = ApplicationBuilder().token(TOKEN).build()
    
    # الروابط (Handlers)
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), download_video))
    
    print("Bot is polling...")
    application.run_polling()

if __name__ == '__main__':
    main()
