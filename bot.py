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
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes

# --- الإعدادات ---
TOKEN = '8668387351:AAHhKiD9RmBjfUNSREdu0KnSddcMxFPExBQ'

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)
executor = ThreadPoolExecutor(max_workers=20)

# --- سيرفر Health Check لضمان استقرار Render ---
def run_health_check():
    PORT = int(os.environ.get("PORT", 8080))
    handler = http.server.SimpleHTTPRequestHandler
    socketserver.TCPServer.allow_reuse_address = True
    try:
        with socketserver.TCPServer(("", PORT), handler) as httpd:
            httpd.serve_forever()
    except Exception as e:
        logger.error(f"Health Check Error: {e}")

# --- دالة التحميل المعدلة لتشمل الفيديو أو الصوت ---
def download_content(url, download_path, mode):
    if mode == "video":
        ydl_opts = {
            'format': 'best[height<=720][ext=mp4]/best[ext=mp4]/best',
            'outtmpl': download_path,
            'noplaylist': True,
            'quiet': True,
            'nocheckcertificate': True,
        }
    else:  # تحميل صوت MP3
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': download_path.replace('.mp4', ''), # سيقوم yt-dlp بإضافة الامتداد
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'quiet
