
import os
import asyncio
import logging
import yt_dlp
from threading import Thread
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, constants
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler

# --- إعداد السجلات (Logging) للمراقبة الاحترافية ---
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# --- 1. خادم الويب (Optimized for Render/Cron-job) ---
app = Flask('')

@app.route('/')
def health_check():
    return "🚀 Bazel Professional Bot is Online", 200

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    server = Thread(target=run_flask)
    server.daemon = True
    server.start()

# --- 2. المحرك الرئيسي للتحميل (Advanced Core) ---

TOKEN = '8668387351:AAHhKiD9RmBjfUNSREdu0KnSddcMxFPExBQ'

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    await update.message.reply_text(
        f"🙋‍♂️ أهلاً بك يا {user.first_name} في **بوت بازل الاحترافي**\n\n"
        "📍 أرسل رابط الفيديو (YouTube, Instagram, TikTok...)\n"
        "⚡ وسأقوم بالمعالجة فوراً بأعلى دقة متوفرة.",
        parse_mode=constants.ParseMode.MARKDOWN
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text
    if not url.startswith(("http://", "https://")):
        return

    # حفظ الرابط بشكل آمن لكل مستخدم
    context.user_data['url'] = url

    keyboard = [
        [
            InlineKeyboardButton("🎬 فيديو (4K/HD)", callback_data='vid'),
            InlineKeyboardButton("🎵 صوت (MP3)", callback_data='aud')
        ]
    ]
    await update.message.reply_text(
        "💎 **اختر صيغة التحميل المطلوبة:**",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode=constants.ParseMode.MARKDOWN
    )

async def process_download(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    url =
