import os
import logging
import tempfile
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    Updater, CommandHandler, MessageHandler, 
    Filters, ConversationHandler, CallbackContext
)
from docx import Document
from docx.shared import Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH
import qrcode
from io import BytesIO
from datetime import datetime

# تمكين التسجيل
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# مراحل المحادثة
START_CHOICE, NAME, PHONE, EMAIL, ADDRESS, CAREER_OBJECTIVE, EDUCATION, EXPERIENCE, SKILLS, LANGUAGES, TEMPLATE, REVIEW, PAYMENT = range(13)

# بيانات المستخدم
user_data = {}
cv_file_path = None

# أزرار تفاعلية
def create_keyboard(options):
    return ReplyKeyboardMarkup([[option] for option in options], one_time_keyboard=True, resize_keyboard=True)

# إنشاء باركود البنك
def generate_bank_qr():
    try:
        bank_data = """
        البنك: الراجحي
        المستفيد: عمر محمد السهلي
        IBAN: SA0080000000000000000000
        المبلغ: 25 ريال
        """
        
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        
        qr.add_data(bank_data)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        qr_path = os.path.join(tempfile.gettempdir(), "bank_qr.png")
        img.save(qr_path)
        
        return qr_path
    except Exception as e:
        logger.error(f"QR generation error: {e}")
        return None

def start(update, context):
    global cv_file_path
    user_data.clear()
    cv_file_path = None
    
    welcome_msg = (
        "🎯 **مرحباً بك في بوت السيرة الذاتية الاحترافية!**\n\n"
        "سأساعدك في إنشاء سيرة ذاتية إنجليزية احترافية.\n\n"
        "💰 **سعر الخدمة: 25 ريال سعودي**\n\n"
        "🚀 **اختر طريقة البدء:**"
    )
    
    update.message.reply_text(welcome_msg, reply_markup=create_keyboard(['📝 بدء إنشاء السيرة', 'ℹ️ معلومات عن البوت']))
    return START_CHOICE

def start_choice(update, context):
    choice = update.message.text
    
    if choice == '📝 بدء إنشاء السيرة':
        update.message.reply_text(
            "👤 **ما هو اسمك بالكامل؟**",
            reply_markup=create_keyboard(['رجوع'])
        )
        return NAME
        
    elif choice == 'ℹ️ معلومات عن البوت':
        info_msg = (
            "🤖 **معلومات عن البوت:**\n\n"
            "• إنشاء سيرة ذاتية إنجليزية احترافية\n"
            "• تصميم ATS-friendly\n"
            "• 3 قوالب مختلفة للاختيار\n"
            "• إمكانية الرجوع والتعديل\n\n"
            "💰 **السعر: 25 ريال سعودي**\n\n"
            "🎯 **للبَدء، اختر 'بدء إنشاء السيرة'**"
        )
        update.message.reply_text(info_msg, reply_markup=create_keyboard(['📝 بدء إنشاء السيرة', 'رجوع']))
        return START_CHOICE
        
    else:
        update.message.reply_text("❌ اختر من الخيارات المتاحة")
        return START_CHOICE

def get_name(update, context):
    if update.message.text.lower() == 'رجوع':
        update.message.reply_text("🔙 عدنا للقائمة الرئيسية:", reply_markup=create_keyboard(['📝 بدء إنشاء السيرة', 'ℹ️ معلومات عن البوت']))
        return START_CHOICE
        
    user_data['name'] = update.message.text
    update.message.reply_text("📱 **أدخل رقم جوالك:**", reply_markup=create_keyboard(['رجوع']))
    return PHONE

def get_phone(update, context):
    if update.message.text.lower() == 'رجوع':
        update.message.reply_text("🔙 عدنا لسؤال الاسم:\nما هو اسمك بالكامل?")
        return NAME
        
    user_data['phone'] = update.message.text
    update.message.reply_text("📧 **أدخل بريدك الإلكتروني:**", reply_markup=create_keyboard(['رجوع']))
    return EMAIL

def get_email(update, context):
    if update.message.text.lower() == 'رجوع':
        update.message.reply_text("🔙 عدنا لسؤال الجوال:\nأدخل رقم جوالك:")
        return PHONE
        
    user_data['email'] = update.message.text
    update.message.reply_text("🏠 **أدخل عنوانك:**", reply_markup=create_keyboard(['رجوع', 'تخطي']))
    return ADDRESS

def get_address(update, context):
    if update.message.text.lower() == 'رجوع':
        user_data.pop('email', None)
        update.message.reply_text("🔙 عدنا لسؤال الإيميل:\nأدخل بريدك الإلكتروني:")
        return EMAIL
    elif update.message.text.lower() == 'تخطي':
        user_data['address'] = "Medina, Saudi Arabia"
        update.message.reply_text("✅ تم استخدام عنوان افتراضي.")
    else:
        user_data['address'] = update.message.text
    
    objective_msg = (
        "🎯 **أدخل الهدف المهني (Career Objective):**\n\n"
        "💡 **مثال:**\n"
        "To leverage my technical expertise in building digital solutions"
    )
    update.message.reply_text(objective_msg, reply_markup=create_keyboard(['رجوع', 'تخطي']))
    return CAREER_OBJECTIVE

def get_career_objective(update, context):
    if update.message.text.lower() == 'رجوع':
        user_data.pop('address', None)
        update.message.reply_text("🔙 عدنا لسؤال العنوان:\nأدخل عنوانك:")
        return ADDRESS
    elif update.message.text.lower() == 'تخطي':
        user_data['career_objective'] = "Seeking a challenging position to utilize my skills"
        update.message.reply_text("✅ تم استخدام هدف افتراضي.")
    else:
        user_data['career_objective'] = update.message.text
    
    edu_msg = (
        "🎓 **أدخل مؤهلاتك التعليمية:**\n\n"
        "💡 **مثال:**\n"
        "Bachelor of Computer Science - King Saud University - 2022"
    )
    update.message.reply_text(edu_msg, reply_markup=create_keyboard(['رجوع', 'تخطي']))
    return EDUCATION

def get_education(update, context):
    if update.message.text.lower() == 'رجوع':
        user_data.pop('career_objective', None)
        update.message.reply_text("🔙 عدنا لسؤال الهدف المهني:\nأدخل الهدف المهني:")
        return CAREER_OBJECTIVE
    elif update.message.text.lower() == 'تخطي':
        user_data['education'] = "No formal education specified"
        update.message.reply_text("✅ تم تخطي التعليم.")
    else:
        user_data['education'] = update.message.text
    
    exp_msg = (
        "💼 **أدخل خبراتك العملية:**\n\n"
        "💡 **مثال:**\n"
        "Web Developer - Tech Solutions Co. - 2022-2024\n"
        "• Developed web applications using Python\n"
        "• Improved system efficiency by 40%"
    )
    update.message.reply_text(exp_msg, reply_markup=create_keyboard(['رجوع', 'تخطي']))
    return EXPERIENCE

def get_experience(update, context):
    if update.message.text.lower() == 'رجوع':
        user_data.pop('education', None)
        update.message.reply_text("🔙 عدنا لسؤال التعليم:\nأدخل مؤهلاتك التعليمية:")
        return EDUCATION
    elif update.message.text.lower() == 'تخطي':
        user_data['experience'] = "No work experience specified"
        update.message.reply_text("✅ تم تخطي الخبرات.")
    else:
        user_data['experience'] = update.message.text
    
    skills_msg = (
        "🛠️ **أدخل مهاراتك (افصل بينها بفواصل):**\n\n"
        "💡 **مثال:**\n"
        "Python, Django, SQL, JavaScript, Project Management"
    )
    update.message.reply_text(skills_msg, reply_markup=create_keyboard(['رجوع', 'تخطي']))
    return SKILLS

def get_skills(update, context):
    if update.message.text.lower() == 'رجوع':
        user_data.pop('experience', None)
        update.message.reply_text("🔙 عدنا لسؤال الخبرات:\nأدخل خبراتك العملية:")
        return EXPERIENCE
    elif update.message.text.lower() == 'تخطي':
        user_data['skills'] = "No skills specified"
        update.message.reply_text("✅ تم تخطي المهارات.")
    else:
        user_data['skills'] = update.message.text
    
    lang_msg = (
        "🌐 **أدخل اللغات التي تتقنها:**\n\n"
        "💡 **مثال:**\n"
        "Arabic (Native), English (Fluent)"
    )
    update.message.reply_text(lang_msg, reply_markup=create_keyboard(['رجوع', 'تخطي']))
    return LANGUAGES

def get_languages(update, context):
    if update.message.text.lower() == 'رجوع':
        user_data.pop('skills', None)
        update.message.reply_text("🔙 عدنا لسؤال المهارات:\nأدخل مهاراتك:")
        return SKILLS
    elif update.message.text.lower() == 'تخطي':
        user_data['languages'] = "No languages specified"
        update.message.reply_text("✅ تم تخطي اللغات.")
    else:
        user_data['languages'] = update.message.text
    
    template_msg = (
        "🎨 **اختر تصميم السيرة الذاتية:**\n\n"
        "1. **كلاسيكي** - تنسيق تقليدي\n"
        "2. **حديث** - تصميم ATS عصري\n"
        "3. **مبدع** - تصميم أنيق\n\n"
        "أختر رقم القالب (1, 2, 3):"
    )
    
    update.message.reply_text(template_msg, reply_markup=create_keyboard(['1', '2', '3', 'رجوع']))
    return TEMPLATE

def choose_template(update, context):
    if update.message.text.lower() == 'رجوع':
        user_data.pop('languages', None)
        update.message.reply_text("🔙 عدنا لسؤال اللغات:\nأدخل اللغات التي تتقنها:")
        return LANGUAGES
        
    template_choice = update.message.text
    templates = {'1': 'classic', '2': 'modern', '3': 'creative'}
    
    if template_choice in templates:
        user_data['template'] = templates[template_choice]
        
        preview_msg = (
            "📋 **لمحة عن بياناتك:**\n\n"
            f"👤 **الاسم:** {user_data.get('name', 'N/A')}\n"
            f"📞 **الجوال:** {user_data.get('phone', 'N/A')}\n"
            f"📧 **الإيميل:** {user_data.get('email', 'N/A')}\n"
            f"🎯 **الهدف:** {user_data.get('career_objective', 'N/A')[:50]}...\n\n"
            "هل تريد المتابعة وإنشاء السيرة الذاتية?"
        )
        
        update.message.reply_text(preview_msg, reply_markup=create_keyboard(['نعم', 'لا', 'تعديل']))
        return REVIEW
    else:
        update.message.reply_text("❌ اختر رقم صحيح (1, 2, 3)")
        return TEMPLATE

def review_data(update, context):
    choice = update.message.text.lower()
    
    if choice == 'نعم':
        try:
            global cv_file_path
            update.message.reply_text("⏳ جاري إنشاء سيرتك الذاتية...")
            cv_file_path = create_professional_cv(user_data, user_data.get('template', 'modern'))
            
            success_msg = (
                f"✅ **تهانينا {user_data.get('name')}!**\n\n"
                "تم إنشاء سيرتك الذاتية بنجاح 🎉\n\n"
                "💰 **السعر: 25 ريال سعودي**\n\n"
                "أرسل 'تم الدفع' بعد التحويل لاستلام الملف."
            )
            update.message.reply_text(success_msg, reply_markup=create_keyboard(['تم الدفع']))
            return PAYMENT
            
        except Exception as e:
            logger.error(f"CV creation error: {e}")
            update.message.reply_text("❌ حدث خطأ في الإنشاء. حاول /start مرة أخرى.")
            return ConversationHandler.END
            
    elif choice == 'تعديل':
        update.message.reply_text("🔧 اختر ما تريد تعديله:", reply_markup=create_keyboard([
            'الاسم', 'الجوال', 'الإيميل', 'العنوان', 'الهدف', 'التعليم', 'الخبرات', 'المهارات', 'اللغات', 'التصميم'
        ]))
        return REVIEW
        
    else:
        update.message.reply_text("❌ تم إلغاء العملية. اكتب /start للبدء من جديد.")
        return ConversationHandler.END

def check_payment(update, context):
    if "تم الدفع" in update.message.text.lower():
        try:
            # إنشاء وإرسال الباركود
            qr_path = generate_bank_qr()
            
            if qr_path:
                with open(qr_path, 'rb') as qr_file:
                    update.message.reply_photo(
                        photo=qr_file,
                        caption=(
                            "💳 **الدفع عبر البنك:**\n\n"
                            "🔹 البنك: الراجحي\n"
                            "🔹 المستفيد: عمر محمد السهلي\n"  
                            "🔹 IBAN: SA0080000000000000000000\n"
                            "🔹 المبلغ: 25 ريال\n\n"
                            "📸 يمكنك مسح الباركود\n"
                            "✅ بعد التحويل، أرسل 'تم الدفع' مرة أخرى"
                        )
                    )
            else:
                update.message.reply_text(
                    "💳 **الدفع عبر البنك:**\n\n"
                    "🔹 البنك: الراجحي\n"
                    "🔹 المستفيد: عمر محمد السهلي\n"  
                    "🔹 IBAN: SA0080000000000000000000\n"
                    "🔹 المبلغ: 25 ريال\n\n"
                    "✅ بعد التحويل، أرسل 'تم الدفع'"
                )
            
            return PAYMENT
            
        except Exception as e:
            logger.error(f"Payment error: {e}")
            update.message.reply_text("❌ حدث خطأ. حاول /start مرة أخرى.")
            return ConversationHandler.END
    else:
        update.message.reply_text("⚠️ أرسل 'تم الدفع' بعد اكتمال التحويل.")
        return PAYMENT

def create_professional_cv(data, template_name):
    try:
        temp_dir = tempfile.gettempdir()
        cv_filename = f"CV_{data.get('name', 'User').replace(' ', '_')}.docx"
        cv_path = os.path.join(temp_dir, cv_filename)
        
        doc = Document()
        
        if template_name == 'classic':
            apply_classic_template(doc, data)
        elif template_name == 'modern':
            apply_modern_template(doc, data)
        elif template_name == 'creative':
            apply_creative_template(doc, data)
        else:
            apply_modern_template(doc, data)
        
        doc.save(cv_path)
        logger.info(f"CV created: {cv_path}")
        return cv_path
        
    except Exception as e:
        logger.error(f"CV creation error: {e}")
        raise

def apply_modern_template(doc, data):
    style = doc.styles['Normal']
    style.font.name = 'Calibri'
    style.font.size = Pt(11)
    
    title = doc.add_heading('CURRICULUM VITAE', 0)
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    
    contact = doc.add_paragraph()
    contact.alignment = WD_ALIGN_PARAGRAPH.CENTER
    contact.add_run(f"Name: {data.get('name', 'N/A')}\n")
    contact.add_run(f"Phone: {data.get('phone', 'N/A')}\n")
    contact.add_run(f"Email: {data.get('email', 'N/A')}\n")
    contact.add_run(f"Address: {data.get('address', 'N/A')}")
    
    if data.get('career_objective'):
        doc.add_heading('CAREER OBJECTIVE', level=1)
        doc.add_paragraph(data.get('career_objective'))
    
    if data.get('experience') != "No work experience specified":
        doc.add_heading('EXPERIENCE', level=1)
        doc.add_paragraph(data.get('experience'))
    
    if data.get('skills') != "No skills specified":
        doc.add_heading('SKILLS', level=1)
        doc.add_paragraph(data.get('skills'))
    
    if data.get('education') != "No formal education specified":
        doc.add_heading('EDUCATION', level=1)
        doc.add_paragraph(data.get('education'))
    
    if data.get('languages') != "No languages specified":
        doc.add_heading('LANGUAGES', level=1)
        doc.add_paragraph(data.get('languages'))

def apply_classic_template(doc, data):
    doc.add_heading('CURRICULUM VITAE', 0)
    add_section(doc, 'PERSONAL INFO', f"Name: {data.get('name', 'N/A')}\nPhone: {data.get('phone', 'N/A')}\nEmail: {data.get('email', 'N/A')}")
    add_section(doc, 'CAREER OBJECTIVE', data.get('career_objective'))
    add_section(doc, 'EXPERIENCE', data.get('experience'))
    add_section(doc, 'SKILLS', data.get('skills'))
    add_section(doc, 'EDUCATION', data.get('education'))
    add_section(doc, 'LANGUAGES', data.get('languages'))

def apply_creative_template(doc, data):
    title = doc.add_heading('CURRICULUM VITAE', 0)
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    
    add_section(doc, 'PERSONAL INFORMATION', 
                f"Name: {data.get('name', 'N/A')}\n"
                f"Phone: {data.get('phone', 'N/A')}\n"
                f"Email: {data.get('email', 'N/A')}\n"
                f"Address: {data.get('address', 'N/A')}")
    
    add_section(doc, 'PROFESSIONAL SUMMARY', data.get('career_objective'))
    add_section(doc, 'WORK EXPERIENCE', data.get('experience'))
    add_section(doc, 'CORE COMPETENCIES', data.get('skills'))
    add_section(doc, 'EDUCATION', data.get('education'))
    add_section(doc, 'LANGUAGES', data.get('languages'))

def add_section(doc, title, content):
    if content and "No " not in content:
        doc.add_heading(title, level=1)
        doc.add_paragraph(content)

def cancel(update, context):
    update.message.reply_text(
        "❌ تم إلغاء العملية.\n\nاكتب /start للبدء من جديد.",
        reply_markup=ReplyKeyboardRemove()
    )
    return ConversationHandler.END

def error_handler(update, context):
    logger.error(f'Bot error: {context.error}')
    if update and update.message:
        update.message.reply_text("❌ حدث خطأ. حاول /start مرة أخرى.")

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
            entry_points=[CommandHandler('start', start), MessageHandler(Filters.text & ~Filters.command, start)],
            states={
                START_CHOICE: [MessageHandler(Filters.text & ~Filters.command, start_choice)],
                NAME: [MessageHandler(Filters.text & ~Filters.command, get_name)],
                PHONE: [MessageHandler(Filters.text & ~Filters.command, get_phone)],
                EMAIL: [MessageHandler(Filters.text & ~Filters.command, get_email)],
                ADDRESS: [MessageHandler(Filters.text & ~Filters.command, get_address)],
                CAREER_OBJECTIVE: [MessageHandler(Filters.text & ~Filters.command, get_career_objective)],
                EDUCATION: [MessageHandler(Filters.text & ~Filters.command, get_education)],
                EXPERIENCE: [MessageHandler(Filters.text & ~Filters.command, get_experience)],
                SKILLS: [MessageHandler(Filters.text & ~Filters.command, get_skills)],
                LANGUAGES: [MessageHandler(Filters.text & ~Filters.command, get_languages)],
                TEMPLATE: [MessageHandler(Filters.text & ~Filters.command, choose_template)],
                REVIEW: [MessageHandler(Filters.text & ~Filters.command, review_data)],
                PAYMENT: [MessageHandler(Filters.text & ~Filters.command, check_payment)],
            },
            fallbacks=[CommandHandler('cancel', cancel)],
        )
        
        dp.add_handler(conv_handler)
        updater.start_polling()
        logger.info("✅ Bot is running with QR code feature!")
        updater.idle()
        
    except Exception as e:
        logger.error(f"❌ Bot startup error: {e}")

if __name__ == '__main__':
    main()
