import logging
import os
import yt_dlp
import asyncio
import threading
import http.server
import socketserver
from concurrent.futures import ThreadPoolExecutor
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes

# --- الإعدادات الأساسية ---
TOKEN = '8668387351:AAHhKiD9RmBjfUNSREdu0KnSddcMxFPExBQ'

# إعداد السجلات (Logs) لسهولة التتبع
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# استخدام ThreadPool للتحميل دون تعطيل البوت
executor = ThreadPoolExecutor(max_workers=10)

# قاموس لتخزين الروابط لتفادي خطأ Button_data_invalid (الروابط الطويلة)
url_cache = {}

# --- سيرفر Health Check لضمان استقرار Render ومنع التوقف ---
def run_health_check():
    PORT = int(os.environ.get("PORT", 8080))
    class HealthHandler(http.server.SimpleHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"Bot is Live!")
    
    socketserver.TCPServer.allow_reuse_address = True
    try:
        with socketserver.TCPServer(("", PORT), HealthHandler) as httpd:
            logger.info(f"Health Check Server running on port {PORT}")
            httpd.serve_forever()
    except Exception as e:
        logger.error(f"Health Check Server Error: {e}")

threading.Thread(target=run_health_check, daemon=True).start()

# --- المحرك الاحترافي للتحميل (تجاوز حماية يوتيوب) ---
def download_content(url, file_path, mode):
    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'nocheckcertificate': True,
        # استخدام User-Agent حديث ومتغير لتجاوز الحظر
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
        'referer': 'https://www.google.com/',
        'geo_bypass': True,
        'source_address': '0.0.0.0',
    }

    if mode == "video":
        ydl_opts.update({
            'format': 'best[height<=720][ext=mp4]/best[ext=mp4]/best',
            'outtmpl': file_path,
        })
    else:  # وضع الصوت
        ydl_opts.update({
            'format': 'bestaudio/best',
            'outtmpl': file_path.replace('.mp3', ''),
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
        })

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
