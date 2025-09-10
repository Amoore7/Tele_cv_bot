import os
import logging
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

# معلومات الدفع
BANK_INFO = """
✅ للدفع عبر البنك:
- اسم المستفيد: عمر محمد السهلي
- البنك: الراجحي
- رقم الحساب: SA0080000000000000000000

بعد التحويل، أرسل 'تم الدفع' وسأرسل لك السيرة الذاتية فورًا.
"""

def start(update, context):
    user_data.clear()
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
        create_professional_cv(user_data)
        update.message.reply_text(
            f"✅ Thank you {user_data['name']}! Your professional CV is ready.\n\n"
            f"{BANK_INFO}\n"
            "Send 'Payment done' after transfer to receive your file."
        )
        return PAYMENT
    except Exception as e:
        update.message.reply_text("❌ Error creating CV. Please try again.")
        logger.error(f"CV creation error: {e}")
        return ConversationHandler.END

def check_payment(update, context):
    if "payment done" in update.message.text.lower() or "تم الدفع" in update.message.text.lower():
        try:
            with open('professional_cv.docx', 'rb') as doc_file:
                update.message.reply_document(
                    document=doc_file,
                    filename=f"CV_{user_data['name'].replace(' ', '_')}.docx"
                )
            update.message.reply_text("✅ Thank you for using our service!")
        except Exception as e:
            update.message.reply_text("❌ Error sending file. Please try again.")
            logger.error(f"File send error: {e}")
        return ConversationHandler.END
    else:
        update.message.reply_text("⚠️ Please send 'Payment done' after completing the transfer.")
        return PAYMENT

def cancel(update, context):
    update.message.reply_text("❌ Process cancelled.")
    return ConversationHandler.END

def create_professional_cv(data):
    doc = Document()
    
    # Set document style
    style = doc.styles['Normal']
    font = style.font
    font.name = 'Calibri'
    font.size = Pt(11)
    
    # Header - Name
    header = doc.sections[0].header
    header_paragraph = header.paragraphs[0]
    header_paragraph.text = data.get('name', '')
    header_paragraph.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    header_paragraph.style.font.size = Pt(14)
    header_paragraph.style.font.bold = True
    
    # Title
    title = doc.add_heading('CURRICULUM VITAE', 0)
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    title.style.font.size = Pt(16)
    title.style.font.bold = True
    
    # Personal Information
    doc.add_heading('PERSONAL INFORMATION', level=1)
    personal_info = doc.add_paragraph()
    personal_info.add_run('Name: ').bold = True
    personal_info.add_run(data.get('name', 'N/A'))
    personal_info.add_run('\nPhone: ').bold = True
    personal_info.add_run(data.get('phone', 'N/A'))
    personal_info.add_run('\nEmail: ').bold = True
    personal_info.add_run(data.get('email', 'N/A'))
    
    # Education
    doc.add_heading('EDUCATION', level=1)
    education = doc.add_paragraph()
    education.add_run(data.get('education', 'No education information provided'))
    
    # Professional Experience
    doc.add_heading('PROFESSIONAL EXPERIENCE', level=1)
    experience = doc.add_paragraph()
    experience.add_run(data.get('experience', 'No experience information provided'))
    
    # Skills
    doc.add_heading('TECHNICAL SKILLS', level=1)
    skills = doc.add_paragraph()
    skills.add_run(data.get('skills', 'No skills information provided'))
    
    # Languages
    doc.add_heading('LANGUAGES', level=1)
    languages = doc.add_paragraph()
    languages.add_run(data.get('languages', 'No languages information provided'))
    
    # Footer with date
    footer = doc.sections[0].footer
    footer_paragraph = footer.paragraphs[0]
    footer_paragraph.text = f"Generated on {datetime.now().strftime('%Y-%m-%d')}"
    footer_paragraph.alignment = WD_ALIGN_PARAGRagraph.CENTER
    
    doc.save('professional_cv.docx')
    logger.info("Professional CV created successfully")

def error_handler(update, context):
    logger.error(f'Bot error: {context.error}')
    if update and update.message:
        update.message.reply_text('❌ Unexpected error. Please try again.')

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
