import os
import asyncio
import yt_dlp
from threading import Thread
from flask import Flask
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

# --- 1. خادم الويب المصغر (لإبقاء البوت حياً على Render) ---
app = Flask('')

@app.route('/')
def home():
    return "Bot is running perfectly!"

def run():
    # Render يستخدم المتغير PORT تلقائياً
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run)
    t.daemon = True
    t.start()

# --- 2. إعدادات التحميل الاحترافية ---

# ضع التوكن الخاص بك هنا
TOKEN = '8668387351:AAHhKiD9RmBjfUNSREdu0KnSddcMxFPExBQ'

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_text = (
        "🚀 **مرحباً بك في البوت القوي للتحميل!**\n\n"
        "أرسل لي أي رابط من (يوتيوب، تيك توك، فيسبوك، إنستغرام، تويتر، أو أي موقع آخر) "
        "وسأقوم بجلب الفيديو بأفضل جودة ممكنة."
    )
    await update.message.reply_text(welcome_text, parse_mode='Markdown')

async def download_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text
    if not url.startswith("http"):
        return

    status_message = await update.message.reply_text("🔍 جاري الفحص والتحميل بأقصى سرعة...")

    # الإعدادات "الوحشية" لتجاوز الحظر والقيود
    ydl_opts = {
        # اختيار أفضل جودة فيديو وصوت مدمجين بصيغة mp4 لضمان التوافق
        'format': 'best[ext=mp4]/best',
        'outtmpl': 'vid_%(id)s.%(ext)s',
        'cookiefile': 'cookies.txt',  # الحل الجذري لمشكلة "Sign in"
        
        # إعدادات الشبكة المتقدمة
        'socket_timeout': 60,
        'retries': 15,
        'fragment_retries': 15,
        'ignoreerrors': False,
        'no_warnings': True,
        'quiet': True,
        
        # تزييف الهوية للظهور كمتصفح إنسان حقيقي
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
        'referer': 'https://www.google.com/',
        
        # خيارات إضافية للمنصات الصعبة
        'noplaylist': True,
        'geo_bypass': True,
        'extract_flat': False,
    }

    try:
        # استخدام ThreadPoolExecutor لتجنب تجميد البوت أثناء التحميل الثقيل
        loop = asyncio.get_event_loop()
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # استخراج البيانات والتحميل
            info = await loop.run_in_executor(None, lambda: ydl.extract_info(url, download=True))
            filename = ydl.prepare_filename(info)
            
            # التأكد من وجود الملف قبل الإرسال
            if os.path.exists(filename):
                with open(filename, 'rb') as video:
                    await update.message.reply_video(
                        video=video,
                        caption=f"✅ تم التحميل بنجاح!\n\n📌 **العنوان:** {info.get('title', 'غير معروف')}",
                        parse_mode='Markdown'
                    )
                # تنظيف المساحة فوراً
                os.remove(filename)
            
            await status_message.delete()

    except Exception as e:
        error_str = str(e)
        if "Sign in" in error_str:
            msg = "❌ يوتيوب يتطلب تحديث ملف الكوكيز (cookies.txt)."
        elif "Timed out" in error_str:
            msg = "❌ المنصة لا تستجيب (Timeout)، حاول مرة أخرى."
        else:
            msg = f"❌ فشل التحميل. قد يكون الرابط خاصاً أو المنصة محظورة.\nالتفاصيل: {error_str[:50]}..."
        
        await update.message.reply_text(msg)

# --- 3. التشغيل النهائي ---

def main():
    # تشغيل نظام البقاء حياً
    keep_alive()
    
    # بناء التطبيق
    application = ApplicationBuilder().token(TOKEN).build()
    
    # الروابط
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), download_video))
    
    print("🚀 البوت القوي جاهز للعمل...")
    application.run_polling()

if __name__ == '__main__':
    main()
