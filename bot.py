import logging
import os
import yt_dlp
import asyncio
import time
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# --- إعداداتك الخاصة ---
TOKEN = '8512467148:AAEWX7qcBNe0_s_JXXXUYlJXX1RcbBOYuOA'
CHANNEL_ID = '@YourChannelUsername'  # استبدله بيوزر قناتك (مثال: @my_channel)
CHANNEL_URL = 'https://t.me/YourChannelUsername' # رابط القناة
# -------------------------------

# إعداد السجلات
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', 
    level=logging.INFO
)
logger = logging.getLogger(__name__)

async def is_subscribed(user_id, context):
    """التحقق من اشتراك المستخدم في القناة"""
    if not CHANNEL_ID.startswith('@'):
        return True
    try:
        member = await context.bot.get_chat_member(chat_id=CHANNEL_ID, user_id=user_id)
        return member.status in ['member', 'administrator', 'creator']
    except Exception as e:
        logger.error(f"Subscription check error: {e}")
        return False

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        f"مرحباً {update.effective_user.first_name}!\n"
        "🚀 أنا بوت تحميل الفيديو من إنستقرام، تيك توك، ويوتيوب.\n\n"
        "فقط أرسل الرابط وسأقوم بالباقي."
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
    status_msg = await update.message.reply_text('⏳ جاري جلب بيانات الفيديو...')
    
    # اسم ملف فريد لكل عملية
    file_path = f"video_{user_id}_{int(time.time())}.mp4"

    try:
        ydl_opts = {
            # اختيار أفضل جودة متاحة بحيث لا تتجاوز mp4 لسهولة الرفع
            'format': 'best[ext=mp4]/best', 
            'outtmpl': file_path,
            'quiet': True,
            'no_warnings': True,
            'max_filesize': 48 * 1024 * 1024, # تحديد الحد الأقصى 48 ميجا لتجنب مشاكل تيليجرام
        }

        def download():
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])

        # تشغيل التحميل في thread منفصل
        await asyncio.to_thread(download)

        if os.path.exists(file_path):
            await status_msg.edit_text("📤 جاري رفع الفيديو إلى تيليجرام...")
            
            with open(file_path, 'rb') as video:
                await context.bot.send_video(
                    chat_id=update.effective_chat.id,
                    video=video,
                    caption=f"✅ تم التحميل بنجاح!\n🔗 الرابط: {url}",
                    supports_streaming=True
                )
            
            await status_msg.delete()
        else:
            await status_msg.edit_text("❌ لم يتم العثور على فيديو، أو أن حجمه كبير جداً (أكثر من 50MB).")

    except Exception as e:
        logger.error(f"Error: {e}")
        await status_msg.edit_text(f"❌ فشل المعالجة. تأكد من أن الرابط صحيح أو مدعوم.")
    
    finally:
        # حذف الملف دائماً سواء نجح التحميل أو فشل
        if os.path.exists(file_path):
            os.remove(file_path)

def main():
    # بناء التطبيق
    app = Application.builder().token(TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    print("✅ البوت يعمل الآن...")
    app.run_polling(drop_pending_updates=True)

if __name__ == '__main__':
    main()
