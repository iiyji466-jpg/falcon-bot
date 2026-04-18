import logging
import os
import yt_dlp
import asyncio
import time
import threading
import http.server
import socketserver
from concurrent.futures import ThreadPoolExecutor
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# --- الإعدادات ---
TOKEN = '8668387351:AAHhKiD9RmBjfUNSREdu0KnSddcMxFPExBQ'

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)
executor = ThreadPoolExecutor(max_workers=20)

# --- سيرفر Health Check لمنصات الاستضافة ---
def run_health_check():
    PORT = int(os.environ.get("PORT", 8080))
    handler = http.server.SimpleHTTPRequestHandler
    socketserver.TCPServer.allow_reuse_address = True
    try:
        with socketserver.TCPServer(("", PORT), handler) as httpd:
            httpd.serve_forever()
    except Exception as e:
        logger.error(f"Health Check Server Error: {e}")

# --- دالة التحميل المطورة ---
def download_video(url, download_path):
    ydl_opts = {
        # جودة 720p أو أقل لضمان الحجم المناسب لتيليجرام وسرعة الرفع
        'format': 'best[height<=720][ext=mp4]/best[ext=mp4]/best',
        'outtmpl': download_path,
        'noplaylist': True,
        'quiet': True,
        'no_warnings': True,
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'referer': 'https://www.google.com/',
        'nocheckcertificate': True,
        'geo_bypass': True,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])

# --- معالج الرسائل ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🚀 أهلاً بك في بوت بازل للتحميل!\n\nأرسل لي أي رابط فيديو وسأقوم بتحميله لك فوراً.")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text
    if not url.startswith('http'): return

    status_msg = await update.message.reply_text('⏳ جاري التحميل من الرابط... انتظر قليلاً')
    file_path = f"vid_{update.effective_user.id}_{int(time.time())}.mp4"

    try:
        loop = asyncio.get_event_loop()
        # تشغيل التحميل
        await loop.run_in_executor(executor, download_video, url, file_path)

        if os.path.exists(file_path):
            await status_msg.edit_text("📤 جاري رفع المقطع إلى تيليجرام...")
            
            with open(file_path, 'rb') as v:
                # إرسال الفيديو مع الكابشن المطلوب
                await context.bot.send_video(
                    chat_id=
