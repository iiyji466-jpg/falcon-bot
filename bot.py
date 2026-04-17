import logging
import os
import yt_dlp
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from telegram.error import BadRequest

# --- الإعدادات الخاصة بك ---
TOKEN = 'YOUR_BOT_TOKEN_HERE'
CHANNEL_ID = '@YourChannelUsername'  # ضع معرف قناتك هنا (مثال: @my_channel)
CHANNEL_URL = 'https://t.me/YourChannelUsername' # رابط قناتك
# -------------------------

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# وظيفة للتحقق من الاشتراك في القناة
async def is_subscribed(user_id, context):
    try:
        member = await context.bot.get_chat_member(chat_id=CHANNEL_ID, user_id=user_id)
        if member.status in ['member', 'administrator', 'creator']:
            return True
        return False
    except BadRequest:
        return False

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"أهلاً بك في بوت التحميل الخاص بـ {update.effective_user.first_name}!")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    url = update.message.text

    # 1. التحقق من الاشتراك أولاً
    if not await is_subscribed(user_id, context):
        keyboard = [[InlineKeyboardButton("اضغط هنا للاشتراك في القناة ✅", url=CHANNEL_URL)]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            "عذراً، يجب عليك الاشتراك في قناة البوت أولاً لاستخدام الخدمة:",
            reply_markup=reply_markup
        )
        return

    # 2. إذا كان مشتركاً، نبدأ التحميل
    status_msg = await update.message.reply_text('جاري فحص الرابط والتحميل... ⏳')
    
    try:
        # إعدادات yt-dlp للتحميل النظيف
        ydl_opts = {
            'format': 'best',
            'outtmpl': f'vid_{user_id}.%(ext)s',
            'quiet': True,
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)

        # إرسال الفيديو بدون أي روابط دعائية خارجية
        with open(filename, 'rb') as video:
            await context.bot.send_video(
                chat_id=update.effective_chat.id, 
                video=video, 
                caption="تم التحميل بنجاح ✅"
            )
        
        os.remove(filename) # حذف الفيديو من السيرفر فوراً
        await status_msg.delete()

    except Exception as e:
        await status_msg.edit_text("حدث خطأ! تأكد أن الرابط مدعوم (إنستجرام، تيك توك، إلخ).")
        logging.error(f"Error: {e}")

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    print("البوت يعمل الآن بنظام الاشتراك الإجباري الخاص بك...")
    app.run_polling()

if __name__ == '__main__':
    main()
