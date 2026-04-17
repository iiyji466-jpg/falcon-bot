import os
import asyncio
import yt_dlp
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

# التوكن الخاص بك
TOKEN = '8668387351:AAHhKiD9RmBjfUNSREdu0KnSddcMxFPExBQ'

async def download_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text
    if not url.startswith("http"): return

    status_message = await update.message.reply_text("⏳ **انتظر من فضلك... بوت بازل يحمل لك الفيديوهات بدقة 4K**", parse_mode='Markdown')

    ydl_opts = {
        'format': 'bestvideo+bestaudio/best', # طلب أعلى جودة 4K والدمج
        'merge_output_format': 'mp4',
        'outtmpl': 'bazel_video_%(id)s.%(ext)s',
        'cookiefile': 'cookies.txt', # تأكد من رفع هذا الملف لـ GitHub
        'socket_timeout': 60, # حل مشكلة Timed out
        'retries': 15,
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    }

    try:
        loop = asyncio.get_event_loop()
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = await loop.run_in_executor(None, lambda: ydl.extract_info(url, download=True))
            filename = ydl.prepare_filename(info)
            
            if os.path.exists(filename):
                # ملاحظة: إذا تجاوز الملف 50MB لن يرسله تيليجرام (قيود البوتات)
                with open(filename, 'rb') as video:
                    await update.message.reply_video(video=video, caption=f"✅ **تم التحميل بدقة 4K**\n📌 {info.get('title')}", parse_mode='Markdown')
                os.remove(filename)
            await status_message.delete()
    except Exception as e:
        await update.message.reply_text(f"❌ عذراً، حدث خطأ أثناء جلب الفيديو. تأكد من ملف الكوكيز أو الرابط.")

# إعداد تشغيل البوت الأساسي (main) كما في كودك السابق
