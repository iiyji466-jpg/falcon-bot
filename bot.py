import logging
import os
import yt_dlp
import asyncio
import re
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes

# --- التوكن ---
TOKEN = "PUT_YOUR_TOKEN_HERE"

# --- إعداد ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DOWNLOAD_DIR = "downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# --- تخزين حالة المستخدم ---
user_state = {}

# --- UI ---
def main_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🎬 تحميل فيديو", callback_data="video")],
        [InlineKeyboardButton("🎵 تحميل صوت", callback_data="audio")],
        [InlineKeyboardButton("ℹ️ مساعدة", callback_data="help")]
    ])

def back_button():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔙 رجوع", callback_data="back")]
    ])

# --- التحقق ---
def is_valid_url(url):
    return re.match(r'https?://\S+', url)

# --- تحميل ---
def download(url, mode):
    try:
        ydl_opts = {
            'outtmpl': f'{DOWNLOAD_DIR}/%(title).80s.%(ext)s',
            'format': 'best[ext=mp4]/best' if mode == "video" else 'bestaudio/best',
            'quiet': True,
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            file = ydl.prepare_filename(info)
            title = info.get("title")

        return file, title
    except Exception as e:
        logger.error(e)
        return None, None

# --- start ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_state[update.effective_user.id] = None

    text = """
✨ *مرحبا بك في بوت التحميل الاحترافي*

📥 أرسل رابط وسأقوم بتحميله لك بسرعة  
⚡ واجهة ذكية + أداء عالي  

اختر من القائمة:
"""
    await update.message.reply_text(text, reply_markup=main_menu(), parse_mode="Markdown")

# --- الأزرار ---
async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    uid = query.from_user.id

    if query.data == "video":
        user_state[uid] = "video"
        await query.edit_message_text("🎬 أرسل رابط الفيديو", reply_markup=back_button())

    elif query.data == "audio":
        user_state[uid] = "audio"
        await query.edit_message_text("🎵 أرسل رابط الصوت", reply_markup=back_button())

    elif query.data == "help":
        await query.edit_message_text(
            "📌 فقط أرسل رابط\n🎯 اختر النوع\n⚡ سيتم التحميل مباشرة",
            reply_markup=back_button()
        )

    elif query.data == "back":
        user_state[uid] = None
        await query.edit_message_text("🏠 القائمة الرئيسية", reply_markup=main_menu())

# --- استقبال الرابط ---
async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    url = update.message.text

    if not is_valid_url(url):
        return

    mode = user_state.get(uid)

    if not mode:
        await update.message.reply_text("❗ اختر نوع التحميل أولاً", reply_markup=main_menu())
        return

    msg = await update.message.reply_text("⏳ جاري المعالجة...")

    loop = asyncio.get_running_loop()
    file, title = await loop.run_in_executor(None, download, url, mode)

    if not file:
        await msg.edit_text("❌ فشل التحميل")
        return

    try:
        caption = f"✅ *{title}*"

        with open(file, "rb") as f:
            if mode == "video":
                await update.message.reply_video(video=f, caption=caption, parse_mode="Markdown")
            else:
                await update.message.reply_audio(audio=f, caption=caption, parse_mode="Markdown")

        await msg.delete()

    except Exception as e:
        logger.error(e)
        await msg.edit_text("❌ فشل الإرسال")

    finally:
        if os.path.exists(file):
            os.remove(file)

# --- تشغيل ---
def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(buttons))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))

    app.run_polling()

if __name__ == "__main__":
    main()