import os
import asyncio
from threading import Thread
from flask import Flask
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
import yt_dlp

# --- 1. نظام إبقاء البوت مستيقظاً (Flask) ---
app = Flask('')

@app.route('/')
def home():
    return "OK - Bot is Alive"

def run():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run)
    t.daemon = True
    t.start()

# --- 2. إعدادات البوت والتحميل الشامل ---

TOKEN = '8668387351:AAHhKiD9RmBjfUNSREdu0KnSddcMxFPExBQ' 

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🚀 أهلاً بك في البوت الشامل!\nأرسل لي رابط فيديو من أي منصة (يوتيوب، تيك توك، فيسبوك، إنستغرام، إلخ) وسأحاول تحميله لك.")

async def download_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text
    if not url.startswith("http"):
        return

    status_message = await update.message.reply_text("🔍 جاري فحص الرابط والتحميل من المنصة...")

    # إعدادات شاملة لكل المواقع
    ydl_opts = {
        # 'format': اختيار أفضل جودة فيديو وصوت مدمجين بصيغة mp4 لضمان عملها على كل الهواتف
        'format': 'best[ext=mp4]/best', 
        'outtmpl': 'downloaded_video_%(id)s.%(ext)s',
        'quiet': True,
        'no_warnings': True,
        'cookiefile': 'cookies.txt', # ضروري جداً لتخطي حظر المنصات
        # إضافة 'noplaylist' لضمان تحميل فيديو واحد فقط إذا كان الرابط لقائمة تشغيل
        'noplaylist': True,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            
            # إرسال الفيديو
            with open(filename, 'rb') as video:
                await update.message.reply_video(video=video, caption=f"✅ تم التحميل بنجاح\n📌 العنوان: {info.get('title', 'فيديو')}")
            
            # تنظيف الذاكرة
            if os.path.exists(filename):
                os.remove(filename)
                
            await status_message.delete()
            
    except Exception as e:
        await update.message.reply_text(f"❌ عذراً، تعذر التحميل من هذا الرابط.\nالسبب: {str(e)[:200]}...")

# --- 3. تشغيل المحرك الرئيسي ---

def main():
    keep_alive()
    application = ApplicationBuilder().token(TOKEN).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), download_video))
    
    print("The Universal Bot is running...")
    application.run_polling()

if __name__ == '__main__':
    main()
