import os
import logging
from dotenv import load_dotenv
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters

# .env fayldan o'zgaruvchilarni yuklash
load_dotenv()

BOT_TOKEN = os.getenv('BOT_TOKEN')
ADMIN_ID = os.getenv('ADMIN_ID')

if not BOT_TOKEN or not ADMIN_ID:
    print('BOT_TOKEN yoki ADMIN_ID set qilinmagan')
    exit(1)

# Logging sozlash
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# User xabarlarini saqlash uchun (messageId -> userId mapping)
message_user_map = {}


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start komandasi"""
    user_id = update.effective_user.id
    
    # Agar user admin bo'lsa
    if str(user_id) == str(ADMIN_ID):
        await update.message.reply_text('Salom Admin! Userlardan kelgan xabarlarga reply orqali javob bering.')
        return
    
    # Oddiy user uchun
    keyboard = ReplyKeyboardMarkup(
        [['Buyurtma yuborish']],
        resize_keyboard=True
    )
    await update.message.reply_text(
        "Salom! Buyurtma yoki savolingizni yozing.\nAdmin sizga bot orqali javob beradi.",
        reply_markup=keyboard
    )


async def me_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """User ID ni ko'rsatish"""
    await update.message.reply_text(f"Sizning chat ID: {update.effective_user.id}")


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Barcha xabarlarni qayta ishlash"""
    user_id = update.effective_user.id
    
    # Agar admin javob berayotgan bo'lsa (reply orqali)
    if str(user_id) == str(ADMIN_ID) and update.message.reply_to_message:
        original_message_id = update.message.reply_to_message.message_id
        target_user_id = message_user_map.get(original_message_id)
        
        if target_user_id:
            reply_text = update.message.text or '(media)'
            
            try:
                await context.bot.send_message(chat_id=target_user_id, text=reply_text)
                await update.message.reply_text(f'✅ Javob yuborildi → User ID: {target_user_id}')
            except Exception as err:
                logger.error(f"Javob yuborishda xato: {err}")
                await update.message.reply_text("❌ Yuborishda xato. User botni bloklagan bo'lishi mumkin.")
        else:
            await update.message.reply_text("⚠️ Bu xabarga javob berib bo'lmaydi. Faqat userlardan kelgan xabarlarga reply qiling.")
        return
    
    # Agar admin oddiy xabar yozayotgan bo'lsa (reply qilmasdan)
    if str(user_id) == str(ADMIN_ID):
        await update.message.reply_text("ℹ️ Userga javob berish uchun uning xabariga REPLY qiling (javob berish tugmasini bosing).")
        return
    
    # Oddiy userdan kelgan xabar - adminga yuborish
    user = update.effective_user
    user_name = f"{user.first_name or ''} {user.last_name or ''}".strip()
    username = f"@{user.username}" if user.username else "(username yo'q)"
    text = update.message.text or '(media/xabar)'
    
    try:
        # Admin'ga xabarni yuborish
        message_text = (
            f"📩 Yangi xabar:\n\n"
            f"👤 User: {user_name}\n"
            f"🆔 ID: {user_id}\n"
            f"📱 Username: {username}\n\n"
            f"💬 Xabar:\n{text}\n\n"
            f"➡️ Javob berish uchun bu xabarga REPLY qiling."
        )
        sent_message = await context.bot.send_message(chat_id=ADMIN_ID, text=message_text)
        
        # Message ID va User ID ni saqlash
        message_user_map[sent_message.message_id] = user_id
        
        # User'ga tasdiqlash xabari
        await update.message.reply_text('✅ Xabaringiz adminga yuborildi. Tez orada javob berishadi.')
    except Exception as err:
        logger.error(f"Xabar yuborishda xato: {err}")
        await update.message.reply_text("❌ Xatolik yuz berdi. Iltimos qaytadan urinib ko'ring.")


def main():
    """Botni ishga tushirish"""
    # Application yaratish
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Handlerlarni qo'shish
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("me", me_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # Botni ishga tushirish (polling)
    print('Bot ishlamoqda...')
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    main()
