import os
import logging
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler
from docx import Document
from datetime import datetime

# تمكين التسجيل
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# مراحل المحادثة
NAME, PHONE, EMAIL, EDUCATION, EXPERIENCE, SKILLS, LANGUAGES, PAYMENT = range(8)

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

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text(
        "مرحبًا! سأساعدك في إنشاء سيرة ذاتية احترافية.\n"
        "أدخل اسمك بالكامل:"
    )
    return NAME

async def get_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_data['name'] = update.message.text
    await update.message.reply_text("شكرًا! الآن أدخل رقم جوالك:")
    return PHONE

async def get_phone(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_data['phone'] = update.message.text
    await update.message.reply_text("أدخل بريدك الإلكتروني:")
    return EMAIL

async def get_email(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_data['email'] = update.message.text
    await update.message.reply_text("أدخل مؤهلاتك التعليمية:")
    return EDUCATION

async def get_education(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_data['education'] = update.message.text
    await update.message.reply_text("أدخل خبراتك العملية:")
    return EXPERIENCE

async def get_experience(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_data['experience'] = update.message.text
    await update.message.reply_text("أدخل مهاراتك:")
    return SKILLS

async def get_skills(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_data['skills'] = update.message.text
    await update.message.reply_text("أدخل اللغات التي تتقنها:")
    return LANGUAGES

async def get_languages(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
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

async def check_payment(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if "تم الدفع" in update.message.text.lower():
        # إرسال ملف السيرة الذاتية
        with open('cv.docx', 'rb') as doc_file:
            await update.message.reply_document(
                document=doc_file,
                caption="ها هي سيرتك الذاتية الجاهزة! 🎉"
            )
        await update.message.reply_text("شكرًا لاستخدامك خدمتنا!")
        return ConversationHandler.END
    else:
        await update.message.reply_text("لم أستلم تأكيد الدفع بعد. أرسل 'تم الدفع' عند اكتمال التحويل.")
        return PAYMENT

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("تم إلغاء العملية.", reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END

def create_cv(data):
    doc = Document()
    
    # العنوان
    doc.add_heading('Curriculum Vitae', 0)
    
    # المعلومات الشخصية
    doc.add_heading('Personal Information', level=1)
    doc.add_paragraph(f"Name: {data['name']}")
    doc.add_paragraph(f"Phone: {data['phone']}")
    doc.add_paragraph(f"Email: {data['email']}")
    
    # التعليم
    doc.add_heading('Education', level=1)
    doc.add_paragraph(data['education'])
    
    # الخبرة
    doc.add_heading('Experience', level=1)
    doc.add_paragraph(data['experience'])
    
    # المهارات
    doc.add_heading('Skills', level=1)
    doc.add_paragraph(data['skills'])
    
    # اللغات
    doc.add_heading('Languages', level=1)
    doc.add_paragraph(data['languages'])
    
    # حفظ الملف
    doc.save('cv.docx')

def main() -> None:
    # الحصول على التوكن من المتغيرات البيئية
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    if not token:
        logger.error("لم يتم تعيين TELEGRAM_BOT_TOKEN")
        return
    
    # إنشاء التطبيق
    application = Application.builder().token(token).build()
    
    # محادثة
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_name)],
            PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_phone)],
            EMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_email)],
            EDUCATION: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_education)],
            EXPERIENCE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_experience)],
            SKILLS: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_skills)],
            LANGUAGES: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_languages)],
            PAYMENT: [MessageHandler(filters.TEXT & ~filters.COMMAND, check_payment)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )
    
    application.add_handler(conv_handler)
    
    # بدء البوت
    application.run_polling()

if __name__ == '__main__':
    main()
