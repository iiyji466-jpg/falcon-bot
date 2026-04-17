import os
import asyncio
import yt_dlp
from threading import Thread
from flask import Flask
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

# --- 1. خادم الويب (لإبقاء البوت مستيقظاً 24/7) ---
app = Flask('')

@app.route('/')
def home():
    return "Bot is running with 4K support!"

def run():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run)
    t.daemon = True
    t.start()

# --- 2. إعدادات البوت والتحميل بدقة 4K ---

TOKEN = '8668387351:AAHhKiD9RmBjfUNSREdu0KnSddcMxFPExBQ'

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🚀 **مرحباً بك في بوت بازل المطور!**\n\n"
        "أرسل لي أي رابط وسأقوم بتحميله لك بأعلى دقة متوفرة (4K).",
        parse_mode='Markdown'
    )

async def download_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text
    if not url.startswith("http"):
        return

    # رسالة الانتظار التي طلبتها
    status_message = await update.message.reply_text(
        "⏳ انتظر من فضلك... بوت بازل يحمل لك الفيديوهات بدقة 4K"
    )

    # إعدادات التحميل القصوى
    ydl_opts = {
        # طلب أفضل فيديو (حتى 4K) وأفضل صوت ودمجهما
        'format': 'bestvideo+bestaudio/best',
        'merge_output_format': 'mp4',
        'outtmpl': 'bazel_4k_%(id)s.%(ext)s',
        'cookiefile': 'cookies.txt',  # ضروري لتجاوز حظر المنصات
        
        # تحسينات الشبكة وتجاوز الحظر
        'socket_timeout': 60,
        'retries': 20,
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
        
        # استخدام FFmpeg لدمج الصوت والصورة بدقة عالية
        'postprocessors': [{
            'key': 'FFmpegVideoConvertor',
            'preferedformat': 'mp4',
        }],
        'quiet': True,
        'no_warnings': True,
    }

    try:
        loop = asyncio.get_event_loop()
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # التحميل في الخلفية لمنع تعليق البوت
            info = await loop.run_in_executor(None, lambda: ydl.extract_info(url, download=True))
            filename = ydl.prepare_filename(info)

            if os.path.exists(filename):
                # حساب حجم الملف (تيليجرام يسمح بـ 50MB للبوتات العادية)
                file_size = os.path.getsize(filename) / (1024 * 1024)

                if file_size > 50:
                    await update.message.reply_text(
                        f"⚠️ الفيديو جاهز بدقة 4K ولكن حجمه ({file_size:.1f}MB) أكبر من مسموح تيليجرام (50MB).\n"
                        "جرب تحميل فيديوهات أقصر أو استخدام نسخة تيليجرام بريميوم إذا كان متاحاً."
                    )
                else:
                    with open(filename, 'rb') as video:
                        await update.message.reply_video(
                            video=video,
                            caption=f"✅ تم التحميل بواسطة بوت بازل بدقة 4K\n📌 **العنوان:** {info.get('title')}",
                            parse_mode='Markdown'
                        )
                
                # حذف الملف لتوفير مساحة السيرفر
                os.remove(filename)

            await status_message.delete()

    except Exception as e:
        await update.message.reply_text(f"❌ عذراً، حدث خطأ أثناء جلب الفيديو بدقة 4K.\nتأكد من الرابط أو ملف الكوكيز.")
        print(f"Error: {e}")

# --- 3. تشغيل البوت ---

def main():
    keep_alive()
    application = ApplicationBuilder().token(TOKEN).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), download_video))
    
    print("🚀 Bazel 4K Bot is Online!")
    application.run_polling()

if __name__ == '__main__':
    main()
