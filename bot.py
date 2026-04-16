import os
import asyncio
import yt_dlp
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes

# توكن البوت الخاص بك من BotFather
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
        return

    msg = await update.message.reply_text("⏳ جاري معالجة الرابط وتحميل الفيديو... انتظر قليلاً")
    
    try:
        file_path = await download_video(url)
        await update.message.reply_video(
            video=open(file_path, 'rb'), 
            caption="تم التحميل بنجاح بواسطة بوت فالكون 🦅"
        )
        os.remove(file_path) # حذف الملف لتوفير مساحة الخادم
        await msg.delete()
    except Exception as e:
        await update.message.reply_text(f"❌ حدث خطأ غير متوقع. تأكد من أن الرابط مدعوم.")
        if os.path.exists('video.mp4'): os.remove('video.mp4')

def main():
    print("🚀 البوت بدأ العمل...")
    app = Application.builder().token(TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.run_polling()

if __name__ == '__main__':
    main()
