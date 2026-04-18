import logging
import os
import yt_dlp
import asyncio
from threading import Thread
from flask import Flask
from concurrent.futures import ThreadPoolExecutor
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes

# --- إعداد Flask للبقاء حياً (Keep Alive) ---
server = Flask('')

@server.route('/')
def home():
    return "Bot is Running!"

def run_web_server():
    # المنفذ الافتراضي 8080 للمنصات السحابية
    port = int(os.environ.get("PORT", 8080))
    server.run(host='0.0.0.0', port=port)

# --- إعدادات البوت ---
# استبدل هذا التوكن بالتوكن الجديد من @BotFather
TOKEN = 'YOUR_NEW_BOT_TOKEN_HERE'

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# استخدام ThreadPool للتعامل مع التحميلات المتعددة بسرعة
executor = ThreadPoolExecutor(max_workers=20)
url_cache = {}

# --- دالة التحميل الاحترافية ---
def download_content(url, file_path, mode):
    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'nocheckcertificate': True,
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36',
        'geo_bypass': True,
        # تحسين اختيار الصيغ ليكون سريعاً وشاملاً لليوتيوب وغيره
        'format': 'bestvideo[ext=mp4]+bestaudio[m4a]/best[ext=mp4]/best',
        'outtmpl': file_path,
        'merge_output_format': 'mp4',
    }

    if mode == "audio":
        ydl_opts.update({
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
        })

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        return True
    except Exception as e:
        logger.error(f"Download Error: {e}")
        return False

# --- معالجات الأوامر ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_name = update.effective_user.first_name
    await update.message.reply_text(f"مرحباً {user_name}! ⚡\nأرسل لي أي رابط (يوتيوب، إنستغرام، تيك توك، فيسبوك) وسأقوم بتحميله فوراً.")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text
    if not (url.startswith("http://") or url.startswith("https://")):
        return

    # معرف فريد لكل طلب
    link_id = f"{update.effective_user.id}_{update.message.message_id}"
    url_cache[link_id] = url
    
    keyboard = [
        [InlineKeyboardButton("🎬 فيديو MP4", callback_data=f"v_{link_id}"),
         InlineKeyboardButton("🎵 صوت MP3", callback_data=f"a_{link_id}")]
    ]
    await update.message.reply_text("اختر الصيغة التي تريدها:", reply_markup=InlineKeyboardMarkup(keyboard))

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    data = query.data.split("_")
    prefix, link_id = data[0], "_".join(data[1:])
    url = url_cache.get(link_id)

    if not url:
        await query.edit_message_text("❌ انتهت صلاحية الرابط، أرسله مجدداً.")
        return

    mode = "video" if prefix == "v" else "audio"
    ext = "mp4" if mode == "video" else "mp3"
    file_path = f"file_{link_id}.{ext}"

    await query.edit_message_text(f"⏳ جاري التحميل من {mode}... يرجى الانتظار.")

    loop = asyncio.get_event_loop()
    success = await loop.run_in_executor(executor, download_content, url, file_path, mode)

    if success and os.path.exists(file_path):
        try:
            # التحقق من حجم الملف (تلجرام يدعم حتى 50MB للبوتات)
            if os.path.getsize(file_path) > 50 * 1024 * 1024:
                await query.message.reply_text("❌ الملف كبير جداً (أكثر من 50 ميجا)، لا يمكن إرساله عبر تلجرام.")
            else:
                with open(file_path, 'rb') as f:
                    if mode == "video":
                        await context.bot.send_video(chat_id=query.message.chat_id, video=f, caption="تم التحميل بواسطة بوت باسل ✅")
                    else:
                        await context.bot.send_audio(chat_id=query.message.chat_id, audio=f, caption="تم التحميل بواسطة بوت باسل ✅")
        except Exception as e:
            await query.message.reply_text(f"❌ حدث خطأ أثناء الإرسال: {e}")
        finally:
            if os.path.exists(file_path):
                os.remove(file_path)
    else:
        await query.message.reply_text("❌ فشل التحميل. تأكد من أن الرابط عام وليس خاص.")

# --- تشغيل البوت ---
def main():
    # تشغيل خادم الويب في خلفية منفصلة
    Thread(target=run_web_server, daemon=True).start()

    # تشغيل البوت
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(CallbackQueryHandler(button_handler))
    
    logger.info("Bot is starting...")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
