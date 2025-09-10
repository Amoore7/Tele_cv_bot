import os
import logging
import tempfile
from telegram import Update, ReplyKeyboardRemove
from telegram.ext import (
    Updater, CommandHandler, MessageHandler, 
    Filters, ConversationHandler, CallbackContext
)
from docx import Document
from docx.shared import Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH
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
cv_file_path = None  # تخزين مسار الملف

# معلومات الدفع
BANK_INFO = """
✅ للدفع عبر البنك:
- اسم المستفيد: عمر محمد السهلي
- البنك: الراجحي
- رقم الحساب: SA0080000000000000000000

بعد التحويل، أرسل 'تم الدفع' وسأرسل لك السيرة الذاتية فورًا.
"""

def start(update, context):
    global cv_file_path
    user_data.clear()
    cv_file_path = None
    update.message.reply_text(
        "🚀 **CV Professional Bot**\n\n"
        "I will create a professional ATS-friendly CV in English\n\n"
        "Please enter your full name:"
    )
    return NAME

def get_name(update, context):
    user_data['name'] = update.message.text
    update.message.reply_text("Please enter your phone number:")
    return PHONE

def get_phone(update, context):
    user_data['phone'] = update.message.text
    update.message.reply_text("Please enter your email:")
    return EMAIL

def get_email(update, context):
    user_data['email'] = update.message.text
    update.message.reply_text("🎓 Enter your education (Degree, University, Year):\nExample: Bachelor of Computer Science, King Saud University, 2022")
    return EDUCATION

def get_education(update, context):
    user_data['education'] = update.message.text
    update.message.reply_text("💼 Enter your work experience (Position, Company, Duration, Responsibilities):\nExample: Web Developer, Tech Solutions Co., 2022-2024, Developed web applications using Python and Django")
    return EXPERIENCE

def get_experience(update, context):
    user_data['experience'] = update.message.text
    update.message.reply_text("🛠️ Enter your skills (separated by commas):\nExample: Python, Django, MySQL, JavaScript, HTML, CSS, Git")
    return SKILLS

def get_skills(update, context):
    user_data['skills'] = update.message.text
    update.message.reply_text("🌐 Enter languages you speak (with proficiency level):\nExample: Arabic (Native), English (Fluent), Spanish (Basic)")
    return LANGUAGES

def get_languages(update, context):
    user_data['languages'] = update.message.text
    
    try:
        global cv_file_path
        cv_file_path = create_professional_cv(user_data)
        update.message.reply_text(
            f"✅ Thank you {user_data['name']}! Your professional CV is ready.\n\n"
            f"{BANK_INFO}\n"
            "Send 'Payment done' after transfer to receive your file."
        )
        return PAYMENT
    except Exception as e:
        logger.error(f"CV creation error: {e}")
        update.message.reply_text("❌ Error creating CV. Please try /start again.")
        return ConversationHandler.END

def check_payment(update, context):
    global cv_file_path
    if "payment done" in update.message.text.lower() or "تم الدفع" in update.message.text.lower():
        try:
            if cv_file_path and os.path.exists(cv_file_path):
                with open(cv_file_path, 'rb') as doc_file:
                    update.message.reply_document(
                        document=doc_file,
                        filename=f"CV_{user_data.get('name', 'User').replace(' ', '_')}.docx"
                    )
                update.message.reply_text("✅ Thank you for using our service!")
            else:
                update.message.reply_text("❌ CV file not found. Please start over with /start")
        except Exception as e:
            logger.error(f"File send error: {e}")
            update.message.reply_text("❌ Error sending file. Please try /start again.")
        return ConversationHandler.END
    else:
        update.message.reply_text("⚠️ Please send 'Payment done' after completing the transfer.")
        return PAYMENT

def cancel(update, context):
    update.message.reply_text("❌ Process cancelled.")
    return ConversationHandler.END

def create_professional_cv(data):
    try:
        # إنشاء ملف مؤقت
        temp_dir = tempfile.gettempdir()
        cv_filename = f"cv_{datetime.now().strftime('%Y%m%d_%H%M%S')}.docx"
        cv_path = os.path.join(temp_dir, cv_filename)
        
        doc = Document()
        
        # العنوان الرئيسي
        title = doc.add_heading('CURRICULUM VITAE', 0)
        title.alignment = WD_ALIGN_PARAGRAPH.CENTER
        
        # المعلومات الشخصية
        doc.add_heading('PERSONAL INFORMATION', level=1)
        personal_info = doc.add_paragraph()
        personal_info.add_run('Name: ').bold = True
        personal_info.add_run(data.get('name', 'N/A'))
        personal_info.add_run('\nPhone: ').bold = True
        personal_info.add_run(data.get('phone', 'N/A'))
        personal_info.add_run('\nEmail: ').bold = True
        personal_info.add_run(data.get('email', 'N/A'))
        
        # التعليم
        if data.get('education'):
            doc.add_heading('EDUCATION', level=1)
            education = doc.add_paragraph(data.get('education', ''))
        
        # الخبرة العملية
        if data.get('experience'):
            doc.add_heading('PROFESSIONAL EXPERIENCE', level=1)
            experience = doc.add_paragraph(data.get('experience', ''))
        
        # المهارات
        if data.get('skills'):
            doc.add_heading('TECHNICAL SKILLS', level=1)
            skills = doc.add_paragraph(data.get('skills', ''))
        
        # اللغات
        if data.get('languages'):
            doc.add_heading('LANGUAGES', level=1)
            languages = doc.add_paragraph(data.get('languages', ''))
        
        # حفظ الملف
        doc.save(cv_path)
        logger.info(f"CV created successfully at: {cv_path}")
        return cv_path
        
    except Exception as e:
        logger.error(f"Error in create_professional_cv: {e}")
        raise

def error_handler(update, context):
    logger.error(f'Bot error: {context.error}')
    if update and update.message:
        update.message.reply_text('❌ Unexpected error. Please try /start again.')

def main():
    try:
        token = os.getenv('TELEGRAM_BOT_TOKEN')
        if not token:
            logger.error("❌ TELEGRAM_BOT_TOKEN not set")
            return
        
        updater = Updater(token, use_context=True)
        dp = updater.dispatcher
        
        dp.add_error_handler(error_handler)
        
        conv_handler = ConversationHandler(
            entry_points=[CommandHandler('start', start)],
            states={
                NAME: [MessageHandler(Filters.text & ~Filters.command, get_name)],
                PHONE: [MessageHandler(Filters.text & ~Filters.command, get_phone)],
                EMAIL: [MessageHandler(Filters.text & ~Filters.command, get_email)],
                EDUCATION: [MessageHandler(Filters.text & ~Filters.command, get_education)],
                EXPERIENCE: [MessageHandler(Filters.text & ~Filters.command, get_experience)],
                SKILLS: [MessageHandler(Filters.text & ~Filters.command, get_skills)],
                LANGUAGES: [MessageHandler(Filters.text & ~Filters.command, get_languages)],
                PAYMENT: [MessageHandler(Filters.text & ~Filters.command, check_payment)],
            },
            fallbacks=[CommandHandler('cancel', cancel)],
        )
        
        dp.add_handler(conv_handler)
        updater.start_polling()
        logger.info("✅ Bot is running!")
        updater.idle()
        
    except Exception as e:
        logger.error(f"❌ Bot startup error: {e}")

if __name__ == '__main__':
    main()
