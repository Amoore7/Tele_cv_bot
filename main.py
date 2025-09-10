import os
import logging
from telegram import Update, ReplyKeyboardRemove
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

def start(update, context):
    update.message.reply_text(
        "🚀 لنبدأ إنشاء سيرتك الذاتية!\n\n"
        "📝 ملاحظة مهمة: السيرة الذاتية سيتم إنشاؤها باللغة الإنجليزية.\n\n"
        "أدخل اسمك بالكامل:"
    )
    return NAME

def get_name(update, context):
    user_data['name'] = update.message.text
    update.message.reply_text("شكرًا! الآن أدخل رقم جوالك:")
    return PHONE

def get_phone(update, context):
    user_data['phone'] = update.message.text
    update.message.reply_text("أدخل بريدك الإلكتروني:")
    return EMAIL

def get_email(update, context):
    user_data['email'] = update.message.text
    update.message.reply_text("أدخل مؤهلاتك التعليمية:")
    return EDUCATION

def get_education(update, context):
    user_data['education'] = update.message.text
    update.message.reply_text("أدخل خبراتك العملية:")
    return EXPERIENCE

def get_experience(update, context):
    user_data['experience'] = update.message.text
    update.message.reply_text("أدخل مهاراتك:")
    return LANGUAGES

def get_languages(update, context):
    user_data['languages'] = update.message.text
    
    # إنشاء السيرة الذاتية
    create_cv(user_data)
    
    # طلب الدفع
    update.message.reply_text(
        "شكرًا " + user_data['name'] + "! لقد اكتملت سيرتك الذاتية.\n\n" +
        BANK_INFO + "\n" +
        "أرسل 'تم الدفع' بعد التحويل لاستلام الملف."
    )
    return PAYMENT

def check_payment(update, context):
    if "تم الدفع" in update.message.text.lower():
        try:
            with open('cv.docx', 'rb') as doc_file:
                update.message.reply_document(document=doc_file)
            update.message.reply_text("شكرًا لاستخدامك خدمتنا!")
        except Exception as e:
            update.message.reply_text("حدث خطأ في إرسال الملف. حاول مرة أخرى.")
            logger.error(f"Error sending file: {e}")
        return ConversationHandler.END
    else:
        update.message.reply_text("أرسل 'تم الدفع' عند اكتمال التحويل.")
        return PAYMENT

def cancel(update, context):
    update.message.reply_text("تم الإلغاء.")
    return ConversationHandler.END

def create_cv(data):
    try:
        doc = Document()
        doc.add_heading('Curriculum Vitae', 0)
        
        # المعلومات الشخصية
        doc.add_heading('Personal Information', level=1)
        doc.add_paragraph(f"Name: {data.get('name', 'N/A')}")
        doc.add_paragraph(f"Phone: {data.get('phone', 'N/A')}")
        doc.add_paragraph(f"Email: {data.get('email', 'N/A')}")
        
        # التعليم
        doc.add_heading('Education', level=1)
        doc.add_paragraph(data.get('education', 'No education information'))
        
        # الخبرة
        doc.add_heading('Experience', level=1)
        doc.add_paragraph(data.get('experience', 'No experience information'))
        
        # المهارات
        doc.add_heading('Skills', level=1)
        doc.add_paragraph(data.get('languages', 'No skills information'))
        
        # اللغات
        doc.add_heading('Languages', level=1)
        doc.add_paragraph(data.get('languages', 'No languages information'))
        
        doc.save('cv.docx')
        logger.info("تم إنشاء السيرة الذاتية بنجاح")
        
    except Exception as e:
        logger.error(f"Error creating CV: {e}")
        raise

def main():
    try:
        token = os.getenv('TELEGRAM_BOT_TOKEN')
        if not token:
            logger.error("❌ لم يتم تعيين TELEGRAM_BOT_TOKEN")
            return
        
        logger.info("🚀 بدء تشغيل البوت...")
        updater = Updater(token, use_context=True)
        dp = updater.dispatcher
        
        conv_handler = ConversationHandler(
            entry_points=[CommandHandler('start', start)],
            states={
                NAME: [MessageHandler(Filters.text & ~Filters.command, get_name)],
                PHONE: [MessageHandler(Filters.text & ~Filters.command, get_phone)],
                EMAIL: [MessageHandler(Filters.text & ~Filters.command, get_email)],
                EDUCATION: [MessageHandler(Filters.text & ~Filters.command, get_education)],
                EXPERIENCE: [MessageHandler(Filters.text & ~Filters.command, get_experience)],
                LANGUAGES: [MessageHandler(Filters.text & ~Filters.command, get_languages)],
                PAYMENT: [MessageHandler(Filters.text & ~Filters.command, check_payment)],
            },
            fallbacks=[CommandHandler('cancel', cancel)],
        )
        
        dp.add_handler(conv_handler)
        updater.start_polling()
        logger.info("✅ البوت يعمل الآن!")
        updater.idle()
        
    except Exception as e:
        logger.error(f"❌ خطأ في تشغيل البوت: {e}")

if __name__ == '__main__':
    main()
