import os
import asyncio
import yt_dlp
from threading import Thread
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler

# --- 1. خادم الويب المصغر (لإبقاء البوت حياً على Render) ---
app = Flask('')
@app.route('/')
def home(): return "OK"

def run():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run)
    t.daemon = True
    t.start()

# --- 2. إعدادات التحميل والخيارات ---

TOKEN = '8668387351:AAHhKiD9RmBjfUNSREdu0KnSddcMxFPExBQ'

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🚀 **مرحباً بك في بوت بازل!**\nأرسل لي الرابط وسأعطيك خيارات التحميل.", parse_mode='Markdown')

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text
    if not url.startswith("http"): return

    # تخزين الرابط مؤقتاً في ذاكرة البوت لإتاحته للأزرار
    context.user_data['current_url'] = url

    # إنشاء الأزرار للاختيار
    keyboard = [
        [InlineKeyboardButton("🎬 تحميل فيديو (4K)", callback_data='video')],
        [InlineKeyboardButton("🎵 تحميل صوت (MP3)", callback_data='audio')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text("📥 **ماذا تريد أن أحمل لك؟**", reply_markup=reply_markup, parse_mode='Markdown')

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    url = context.user_data.get('current_url')
    choice = query.data # إما 'video' أو 'audio'

    if not url:
        await query.edit_message_text("❌ انتهت صلاحية الطلب، أرسل الرابط مرة أخرى.")
        return

    await query.edit_message_text(f"⏳ **انتظر من فضلك... بوت بازل يحمل لك {'الفيديو بدقة 4K' if choice == 'video' else 'الملف الصوتي'}**", parse_mode='Markdown')

    # إعدادات yt-dlp بناءً على الاختيار
    if choice == 'video':
        ydl_opts = {
            'format': 'bestvideo+bestaudio/best',
            'merge_output_format': 'mp4',
            'outtmpl': 'bazel_video_%(id)s.%(ext)s',
            'cookiefile': 'cookies.txt', # ضروري لحل مشكلة الحظر
            'socket_timeout': 60, # حل مشكلة Timed out
        }
    else: # اختيار الصوت
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': 'bazel_audio_%(id)s.%(ext)s',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'cookiefile': 'cookies.txt',
            'socket_timeout': 60,
        }

    try:
        loop = asyncio.get_event_loop()
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = await loop.run_in_executor(None, lambda: ydl.extract_info(url, download=True))
            filename = ydl.prepare_filename(info)
            if choice == 'audio': filename = filename.rsplit('.', 1)[0] + '.mp3'

            if os.path.exists(filename):
                file_size = os.path.getsize(filename) / (1024 * 1024)
                if file_size > 50: # قيود تيليجرام للبوتات
                    await query.edit_message_text(f"⚠️ الملف حجمه ({file_size:.1f}MB) أكبر من مسموح تيليجرام.")
                else:
                    with open(filename, 'rb') as f:
                        if choice == 'video':
                            await context.bot.send_video(chat_id=query.message.chat_id, video=f, caption="✅ تم تحميل الفيديو!")
                        else:
                            await context.bot.send_audio(chat_id=query.message.chat_id, audio=f, caption="✅ تم تحميل الصوت!")
                os.remove(filename)
    except Exception as e:
        await query.edit_message_text(f"❌ فشل التحميل. تأكد من الكوكيز أو الرابط.")

# --- 3. تشغيل البوت ---
def main():
    keep_alive()
    application = ApplicationBuilder().token(TOKEN).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    application.add_handler(CallbackQueryHandler(button_callback)) # معالج الأزرار
    
    application.run_polling()

if __name__ == '__main__':
    main()
