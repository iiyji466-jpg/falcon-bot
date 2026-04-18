import logging
import os
import yt_dlp
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
from threading import Thread
from http.server import SimpleHTTPRequestHandler
import socketserver

# --- الإعدادات ---
TOKEN = '8668387351:AAHhKiD9RmBjfUNSREdu0KnSddcMxFPExBQ'

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# سيرفر Health Check لمنع توقف Render
def run_health_server():
    port = int(os.environ.get("PORT", 8080))
    with socketserver.TCPServer(("", port), SimpleHTTPRequestHandler) as httpd:
        httpd.serve_forever()

Thread(target=run_health_server, daemon=True).start()

# دالة استخراج الروابط المباشرة
def extract_direct_link(url, mode):
    ydl_opts = {
        'format': 'best[ext=mp4]/best' if mode == "video" else 'bestaudio/best',
        'quiet': True,
        'no_warnings': True,
        'nocheckcertificate': True,
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            return info.get('url'), info.get('title', 'video')
    except:
        return None, None

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🚀 أرسل الرابط، وسأعطيك التحميل فوراً!")

async def handle_msg(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text
    if "http" not in url: return
    
    kb = [[
        InlineKeyboardButton("🎬 فيديو سريع", callback_data=f"v|{url}"),
        InlineKeyboardButton("🎵 صوت MP3", callback_data=f"a|{url}")
    ]]
    await update.message.reply_text("⚡ اختر طريقة التحميل:", reply_markup=InlineKeyboardMarkup(kb))

async def cb_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    data = query.data.split("|")
    mode = "video" if data[0] == "v" else "audio"
    target_url = data[1]

    msg = await query.edit_message_text("⚡ جاري استخراج الرابط المباشر...")

    loop = asyncio.get_event_loop()
    direct_link, title = await loop.run_in_executor(None, extract_direct_link, target_url, mode)

    if direct_link:
        # إنشاء زر المشاركة
        # رابط المشاركة يفتح قائمة جهات الاتصال في تلجرام لإرسال الرابط الأصلي
        share_url = f"https://t.me/share/url?url={target_url}&text=شاهد هذا الفيديو!"
        share_kb = InlineKeyboardMarkup([[
            InlineKeyboardButton("📤 مشاركة الفيديو", url=share_url)
        ]])

        caption_text = f"✅ {title}\n\nشكراً لاستخدامك البوت الخاص بنا! ❤️"

        if mode == "video":
            await query.message.reply_video(video=direct_link, caption=caption_text, reply_markup=share_kb)
        else:
            await query.message.reply_audio(audio=direct_link, caption=caption_text, reply_markup=share_kb)
        
        await msg.delete()
    else:
        await msg.edit_text("❌ فشل الاستخراج السريع. حاول مجدداً.")

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_msg))
    app.add_handler(CallbackQueryHandler(cb_handler))
    app.run_polling(drop_pending_updates=True)

if __name__ == '__main__':
    main()
