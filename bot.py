import os
import asyncio
from threading import Thread
from flask import Flask
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
import yt_dlp

# --- 1. نظام Flask للبقاء مستيقظاً (لـ Render و Cron-job) ---
app = Flask('')

@app.route('/')
def home():
    return "OK"

def run():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run)
    t.daemon = True
    t.start()

# --- 2. إعدادات البوت والتحميل الشامل ---

# ⚠️ ضع التوكن الخاص بك هنا
TOKEN = '8668387351:AAHhKiD9RmBjfUNSREdu0KnSddcMxFPExBQ' 

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🚀 أهلاً بك في بوت التحميل العالمي!\nأرسل لي أي رابط فيديو (يوتيوب، إنستغرام، تيك توك، إلخ) وسأقوم بتحميله.")

async def download_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text
    if not url.startswith("http"):
        return

    status_message = await update.message.reply_text("⏳ جاري المعالجة والتحميل... قد يستغرق الأمر ثوانٍ.")

    # الإعدادات المتقدمة التي طلبتها:
    ydl_opts = {
        'format': 'best[ext=mp4]/best',
        'outtmpl': 'video_%(id)s.%(ext)s',
        'cookiefile': 'cookies.txt',
        'socket_timeout': 30,
        'retries': 10,
        'fragment_retries': 10,
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'quiet': True,
        'no_warnings': True,
        'noplaylist': True,
        'extract_flat': False,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # استخراج المعلومات والتحميل
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            
            # إرسال الفيديو للمستخدم
            with open(filename, 'rb') as video:
                await update.message.reply_video(
                    video=video, 
                    caption=f"✅ تم التحميل بنجاح!\n📌 {info.get('title', 'فيديو')}"
                )
            
            # مسح الفيديو من السيرفر فوراً لتوفير المساحة
            if os.path.exists(filename):
                os.remove(filename)
                
            await status_message.delete()
            
    except Exception as e:
        error_msg = str(e)
        # تخصيص رسالة الخطأ لتكون أوضح
        if "Sign in" in error_msg:
            await update.message.reply_text("❌ يوتيوب يطلب تسجيل الدخول. يرجى تحديث ملف cookies.txt")
        elif "Timed out" in error_msg:
            await update.message.reply_text("❌ المنصة استغرقت وقتاً طويلاً للرد. حاول مرة أخرى لاحقاً.")
        else:
            await update.message.reply_text(f"❌ عذراً، حدث خطأ: {error_msg[:100]}...")

# --- 3. تشغيل كل شيء ---

def main():
    # تشغيل سيرفر الويب في الخلفية
    keep_alive()
    print("Web server started.")

    # تشغيل البوت
    application = ApplicationBuilder().token(TOKEN).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), download_video))
    
    print("Bot is polling...")
    application.run_polling()

if __name__ == '__main__':
    main()
