import os
import asyncio
import yt_dlp
from flask import Flask
from threading import Thread
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes

# --- كود إبقاء البوت يعمل دائماً على Render ---
app = Flask('')

@app.route('/')
def home():
    return "Bot is Online and Alive!"

def run():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run)
    t.daemon = True
    t.start()

keep_alive()
# ---------------------------------------------

TOKEN = '8668387351:AAHhKiD9RmBjfUNSREdu0KnSddcMxFPExBQ'

async def download_video(url):
    ydl_opts = {
        'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
        'outtmpl': 'video.%(ext)s',
        'quiet': True,
        'no_warnings': True,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        return ydl.prepare_filename(info)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text
    if not url.startswith('http'):
        await update.message.reply_text("من فضلك أرسل رابط فيديو صحيح.")
        return

    msg = await update.message.reply_text("جاري التحميل... انتظر قليلاً ⏳")
    
    try:
        file_path = await download_video(url)
        await update.message.reply_video(video=open(file_path, 'rb'))
        if os.path.exists(file_path):
            os.remove(file_path)
        await msg.delete()
    except Exception as e:
        await msg.edit_text(f"حدث خطأ أثناء التحميل: {str(e)}")

def main():
    application = Application.builder().token(TOKEN).build()
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("البوت يعمل الآن...")
    application.run_polling()

if __name__ == '__main__':
    main()
