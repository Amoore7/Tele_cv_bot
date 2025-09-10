import os
import logging
import re
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    Updater, CommandHandler, MessageHandler, 
    Filters, ConversationHandler, CallbackContext
)
from docx import Document

# تمكين التسجيل
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# مراحل المحادثة
NAME, PHONE, EMAIL, EDUCATION, EXPERIENCE, LANGUAGES, PAYMENT = range(7)

# بيانات المستخدم
user_data = {}

# معلومات الدفع
BANK_INFO = """
✅ للدفع عبر البنك:
- اسم المستفيد: عمر محمد السهلي
- البنك: الراجحي
- رقم الحساب: SA0080000000000000000000

بعد التحويل، أرسل 'تم الدفع' وسأرسل لك السيرة الذاتية فورًا.
"""

async def start(update: Update, context: CallbackContext) -> int:
    await update.message.reply_text(
        "🚀 **لنبدأ إنشاء سيرتك الذاتية!**\n\n"
        "📝 **ملاحظة مهمة:** السيرة الذاتية سيتم إنشاؤها باللغة الإنجليزية.\n\n"
        "أدخل اسمك بالكامل:"
    )
    return NAME

async def get_name(update: Update, context: CallbackContext) -> int:
    user_data['name'] = update.message.text
    await update.message.reply_text("شكرًا! الآن أدخل رقم جوالك:")
    return PHONE

async def get_phone(update: Update, context: CallbackContext) -> int:
    user_data['phone'] = update.message.text
    await update.message.reply_text("أدخل بريدك الإلكتروني:")
    return EMAIL

async def get_email(update: Update, context: CallbackContext) -> int:
    user_data['email'] = update.message.text
    await update.message.reply_text("أدخل مؤهلاتك التعليمية:")
    return EDUCATION

async def get_education(update: Update, context: CallbackContext) -> int:
    user_data['education'] = update.message.text
    await update.message.reply_text("أدخل خبراتك العملية:")
    return EXPERIENCE

async def get_experience(update: Update, context: CallbackContext) -> int:
    user_data['experience'] = update.message.text
    await update.message.reply_text("أدخل مهاراتك:")
    return LANGUAGES

async def get_languages(update: Update, context: CallbackContext) -> int:
    user_data['languages'] = update.message.text
    
    # إنشاء السيرة الذاتية
    create_cv(user_data)
    
    # طلب الدفع
    await update.message.reply_text(
        f"شكرًا {user_data['name']}! لقد اكتملت سيرتك الذاتية.\n\n"
        f"{BANK_INFO}\n"
        "أرسل 'تم الدفع' بعد التحويل لاستلام الملف."
    )
    return PAYMENT

async def check_payment(update: Update, context: CallbackContext) -> int:
    if "تم الدفع" in update.message.text.lower():
        with open('cv.docx', 'rb') as doc_file:
            await update.message.reply_document(document=doc_file)
        await update.message.reply_text("شكرًا لاستخدامك خدمتنا!")
        return ConversationHandler.END
    else:
        await update.message.reply_text("أرسل 'تم الدفع' عند اكتمال التحويل.")
        return PAYMENT

async def cancel(update: Update, context: CallbackContext) -> int:
    await update.message.reply_text("تم الإلغاء.")
    return ConversationHandler.END

def create_cv(data):
    doc = Document()
    doc.add_heading('Curriculum Vitae', 0)
    doc.add_heading('Personal Information', level=1)
    doc.add_paragraph(f"Name: {data['name']}")
    doc.add_paragraph(f"Phone: {data['phone']}")
    doc.add_paragraph(f"Email: {data['email']}")
    doc.add_heading('Education', level=1)
    doc.add_paragraph(data['education'])
    doc.add_heading('Experience', level=1)
    doc.add_paragraph(data['experience'])
    doc.add_heading('Skills', level=1)
    doc.add_paragraph(data.get('skills', 'No skills provided'))
    doc.add_heading('Languages', level=1)
    doc.add_paragraph(data['languages'])
    doc.save('cv.docx')

def main() -> None:
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    if not token:
        logger.error("لم يتم تعيين TELEGRAM_BOT_TOKEN")
        return
    
    updater = Updater(token, use_context=True)
    dp = updater.dispatcher
    
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            NAME: [MessageHandler(Filters.text, get_name)],
            PHONE: [MessageHandler(Filters.text, get_phone)],
            EMAIL: [MessageHandler(Filters.text, get_email)],
            EDUCATION: [MessageHandler(Filters.text, get_education)],
            EXPERIENCE: [MessageHandler(Filters.text, get_experience)],
            LANGUAGES: [MessageHandler(Filters.text, get_languages)],
            PAYMENT: [MessageHandler(Filters.text, check_payment)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )
    
    dp.add_handler(conv_handler)
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
