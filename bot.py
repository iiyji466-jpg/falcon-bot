import logging
import os
import yt_dlp
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from telegram.error import BadRequest, NetworkError

# --- إعداداتك الخاصة (يجب ملؤها) ---
TOKEN = '8512467148:AAEWX7qcBNe0_s_JXXXUYlJXX1RcbBOYuOA'
CHANNEL_ID = '@YourChannelUsername'  # غير هذا ليوزر قناتك
CHANNEL_URL = 'https://t.me/YourChannelUsername'
# -------------------------------

# إعداد السجلات لمراقبة أداء البوت
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', 
    level=logging.INFO
)

async def is_subscribed(user_id, context):
    """التحقق من اشتراك المستخدم في القناة"""
    if CHANNEL_ID.startswith('@'):
        try:
            member = await context.bot.get_chat_member(chat_id=CHANNEL_ID, user_id=user_id)
            return member.status in ['member', 'administrator', 'creator']
        except Exception:
            return False
    return True # إذا لم تضع قناة، سيعمل البوت للجميع

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        f"مرحباً {update.effective_user.first_name}!\n"
        "أرسل لي رابط فيديو (Instagram, TikTok, YouTube) وسأقوم بتحميله فوراً."
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    url = update.message.text

    # 1. فحص الاشتراك الإجباري
    if not await is_subscribed(user_id, context):
        keyboard = [[InlineKeyboardButton("الاشتراك في القناة ✅", url=CHANNEL_URL)]]
        await update.message.reply_text(
            "⚠️ عذراً! يجب عليك الاشتراك في القناة أولاً لتتمكن من استخدام البوت.",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return

    # 2. بدء عملية التحميل
    status_msg = await update.message.reply_text('🚀 جاري المعالجة... انتظر ثوانٍ')
    file_path = f"vid_{user_id}_{os.getpid()}.mp4"

    try:
        # إعدادات yt-dlp قوية لتجاوز الحظر وجلب أفضل جودة
        ydl_opts = {
            'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
            'outtmpl': file_path,
            'quiet': True,
            'no_warnings': True,
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
        }

        # تنفيذ التحميل في خيط (Thread) منفصل لعدم تجميد البوت
        def download():
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])

        await asyncio.to_thread(download)

        # 3. إرسال الفيديو
        if os.path.exists(file_path):
            await status_msg.edit_text("📤 جاري الرفع إلى تيليجرام...")
            with open(file_path, 'rb') as video:
                await context.bot.send_video(
                    chat_id=update.effective_chat.id,
                    video=video,
                    caption="✅ تم التحميل بنجاح بواسطة بوتك الخاص.",
                    supports_streaming=True
                )
            os.remove(file_path) # حذف الملف لتوفير مساحة السيرفر
            await status_msg.delete()
        else:
            await status_msg.edit_text("❌ عذراً، لم أتمكن من العثور على الفيديو.")

    except Exception as e:
        logging.error(f"Download Error: {e}")
        if os.path.exists(file_path): os.remove(file_path)
        await status_msg.edit_text("❌ فشل التحميل. قد يكون الرابط خاصاً أو غير مدعوم.")

def main():
    # بناء التطبيق مع إعدادات إعادة الاتصال التلقائي
    app = Application.builder().token(TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    print("✅ البوت يعمل الآن بأقصى قوة على Render...")
    app.run_polling(drop_pending_updates=True)

if __name__ == '__main__':
    main()
