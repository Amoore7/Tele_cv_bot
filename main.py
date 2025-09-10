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
from datetime import datetime

# تمكين التسجيل
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# مراحل المحادثة
NAME, PHONE, EMAIL, EDUCATION, EXPERIENCE, SKILLS, LANGUAGES, REVIEW, PAYMENT = range(9)

# بيانات المستخدم
user_data = {}
cv_file_path = None

# معلومات الدفع
BANK_INFO = """
✅ للدفع عبر البنك:
- اسم المستفيد: عمر محمد السهلي
- البنك: الراجحي  
- رقم الحساب: SA0080000000000000000000

بعد التحويل، أرسل 'تم الدفع' لاستلام السيرة الذاتية.
"""

# أزرار تفاعلية
def create_keyboard(options):
    return ReplyKeyboardMarkup([[option] for option in options], one_time_keyboard=True, resize_keyboard=True)

def start(update, context):
    global cv_file_path
    user_data.clear()
    cv_file_path = None
    
    welcome_msg = (
        "🎯 **مرحباً بك في بوت السيرة الذاتية الاحترافية!**\n\n"
        "سأساعدك في إنشاء سيرة ذاتية إنجليزية احترافية.\n\n"
        "📝 للإجابة على الأسئلة، يمكنك:\n"
        "• الكتابة مباشرة\n"  
        "• استخدام الأزرار للاختيار\n"
        "• كتابة 'رجوع' للعودة للخلف\n"
        "• كتابة 'إلغاء' للخروج\n\n"
        "🚀 **لنبدأ! ما هو اسمك بالكامل؟**"
    )
    
    update.message.reply_text(welcome_msg, reply_markup=ReplyKeyboardRemove())
    return NAME

def get_name(update, context):
    if update.message.text.lower() in ['رجوع', 'back']:
        update.message.reply_text("أنت في البداية بالفعل!")
        return NAME
        
    user_data['name'] = update.message.text
    
    next_msg = (
        "👌 تم حفظ الاسم.\n\n"
        "📱 **الآن أدخل رقم جوالك:**\n"
        "مثال: 0512345678"
    )
    update.message.reply_text(next_msg, reply_markup=create_keyboard(['رجوع']))
    return PHONE

def get_phone(update, context):
    if update.message.text.lower() == 'رجوع':
        user_data.pop('name', None)
        update.message.reply_text("🔙 عدنا لسؤال الاسم:\nما هو اسمك بالكامل؟")
        return NAME
        
    user_data['phone'] = update.message.text
    
    next_msg = (
        "✅ تم حفظ الجوال.\n\n"
        "📧 **أدخل بريدك الإلكتروني:**\n"
        "مثال: name@example.com"
    )
    update.message.reply_text(next_msg, reply_markup=create_keyboard(['رجوع']))
    return EMAIL

def get_email(update, context):
    if update.message.text.lower() == 'رجوع':
        user_data.pop('phone', None)
        update.message.reply_text("🔙 عدنا لسؤال الجوال:\nأدخل رقم جوالك:")
        return PHONE
        
    user_data['email'] = update.message.text
    
    edu_example = (
        "🎓 **أدخل مؤهلاتك التعليمية:**\n\n"
        "💡 **مثال:**\n"
        "البكالوريوس في علوم الحاسب - جامعة الملك سعود - 2022\n"
        "الدبلوم في إدارة الأعمال - الكلية التقنية - 2020"
    )
    update.message.reply_text(edu_example, reply_markup=create_keyboard(['رجوع', 'تخطي']))
    return EDUCATION

def get_education(update, context):
    if update.message.text.lower() == 'رجوع':
        user_data.pop('email', None)
        update.message.reply_text("🔙 عدنا لسؤال الإيميل:\nأدخل بريدك الإلكتروني:")
        return EMAIL
    elif update.message.text.lower() == 'تخطي':
        user_data['education'] = "No formal education"
        update.message.reply_text("✅ تم تخطي التعليم.")
    else:
        user_data['education'] = update.message.text
    
    exp_example = (
        "💼 **أدخل خبراتك العملية:**\n\n"
        "💡 **مثال:**\n"
        "مطور ويب - شركة التقنية - 2022-2024\n"
        "• تطوير تطبيقات ويب باستخدام Python\n"
        "• إدارة قواعد البيانات\n"
        "• العمل مع فرق Agile"
    )
    update.message.reply_text(exp_example, reply_markup=create_keyboard(['رجوع', 'تخطي']))
    return EXPERIENCE

def get_experience(update, context):
    if update.message.text.lower() == 'رجوع':
        user_data.pop('education', None)
        update.message.reply_text("🔙 عدنا لسؤال التعليم:\nأدخل مؤهلاتك التعليمية:")
        return EDUCATION
    elif update.message.text.lower() == 'تخطي':
        user_data['experience'] = "No work experience"
        update.message.reply_text("✅ تم تخطي الخبرات.")
    else:
        user_data['experience'] = update.message.text
    
    skills_example = (
        "🛠️ **أدخل مهاراتك (افصل بينها بفواصل):**\n\n"
        "💡 **مثال:**\n"
        "برمجة Python, تطوير الويب, قواعد البيانات, إدارة المشاريع"
    )
    update.message.reply_text(skills_example, reply_markup=create_keyboard(['رجوع', 'تخطي']))
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
    
    lang_example = (
        "🌐 **أدخل اللغات التي تتقنها:**\n\n"
        "💡 **مثال:**\n"
        "العربية (ممتاز), الإنجليزية (جيد), الفرنسية (مبتدئ)"
    )
    update.message.reply_text(lang_example, reply_markup=create_keyboard(['رجوع', 'تخطي']))
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
    
    # معاينة البيانات
    preview_msg = (
        "📋 **لمحة عن بياناتك:**\n\n"
        f"👤 **الاسم:** {user_data.get('name', 'N/A')}\n"
        f"📞 **الجوال:** {user_data.get('phone', 'N/A')}\n"
        f"📧 **الإيميل:** {user_data.get('email', 'N/A')}\n"
        f"🎓 **التعليم:** {user_data.get('education', 'N/A')}\n"
        f"💼 **الخبرات:** {user_data.get('experience', 'N/A')}\n"
        f"🛠️ **المهارات:** {user_data.get('skills', 'N/A')}\n"
        f"🌐 **اللغات:** {user_data.get('languages', 'N/A')}\n\n"
        "هل تريد المتابعة وإنشاء السيرة الذاتية؟"
    )
    
    update.message.reply_text(preview_msg, reply_markup=create_keyboard(['نعم', 'لا', 'تعديل']))
    return REVIEW

def review_data(update, context):
    choice = update.message.text.lower()
    
    if choice == 'نعم':
        try:
            global cv_file_path
            cv_file_path = create_professional_cv(user_data)
            
            success_msg = (
                f"✅ **تهانينا {user_data.get('name')}!**\n\n"
                "تم إنشاء سيرتك الذاتية بنجاح 🎉\n\n"
                f"{BANK_INFO}\n\n"
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
            'الاسم', 'الجوال', 'الإيميل', 'التعليم', 'الخبرات', 'المهارات', 'اللغات'
        ]))
        return REVIEW
        
    else:  # لا أو أي رد آخر
        update.message.reply_text("❌ تم إلغاء العملية. اكتب /start للبدء من جديد.")
        return ConversationHandler.END

def check_payment(update, context):
    if "تم الدفع" in update.message.text.lower():
        try:
            if cv_file_path and os.path.exists(cv_file_path):
                with open(cv_file_path, 'rb') as doc_file:
                    update.message.reply_document(
                        document=doc_file,
                        filename=f"CV_{user_data.get('name', 'User')}.docx",
                        caption="🎉 **ها هي سيرتك الذاتية الجاهزة!**\n\nشكراً لثقتك بنا 🌟"
                    )
                update.message.reply_text("✅ تم الإرسال بنجاح! اكتب /start لإنشاء سيرة جديدة.")
            else:
                update.message.reply_text("❌ لم يتم العثور على الملف. اكتب /start للبدء من جديد.")
        except Exception as e:
            logger.error(f"File send error: {e}")
            update.message.reply_text("❌ خطأ في الإرسال. حاول /start مرة أخرى.")
        return ConversationHandler.END
    else:
        update.message.reply_text("⚠️ أرسل 'تم الدفع' بعد اكتمال التحويل.")
        return PAYMENT

def cancel(update, context):
    update.message.reply_text(
        "❌ تم إلغاء العملية.\n\n"
        "اكتب /start عندما تكون جاهزاً للبدء 🚀",
        reply_markup=ReplyKeyboardRemove()
    )
    return ConversationHandler.END

def create_professional_cv(data):
    try:
        temp_dir = tempfile.gettempdir()
        cv_filename = f"cv_{datetime.now().strftime('%Y%m%d_%H%M%S')}.docx"
        cv_path = os.path.join(temp_dir, cv_filename)
        
        doc = Document()
        
        # العنوان
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
        
        # الأقسام الأخرى
        sections = [
            ('EDUCATION', 'education'),
            ('PROFESSIONAL EXPERIENCE', 'experience'),
            ('SKILLS', 'skills'),
            ('LANGUAGES', 'languages')
        ]
        
        for section_title, data_key in sections:
            if data.get(data_key) and data[data_key] != "No " + data_key + " specified":
                doc.add_heading(section_title, level=1)
                doc.add_paragraph(data[data_key])
        
        doc.save(cv_path)
        logger.info(f"CV created: {cv_path}")
        return cv_path
        
    except Exception as e:
        logger.error(f"CV creation error: {e}")
        raise

def error_handler(update, context):
    logger.error(f'Bot error: {context.error}')
    if update and update.message:
        update.message.reply_text(
            "❌ حدث خطأ غير متوقع.\n\n"
            "اكتب /start للمحاولة مرة أخرى 🔄"
        )

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
                REVIEW: [MessageHandler(Filters.text & ~Filters.command, review_data)],
                PAYMENT: [MessageHandler(Filters.text & ~Filters.command, check_payment)],
            },
            fallbacks=[CommandHandler('cancel', cancel)],
        )
        
        dp.add_handler(conv_handler)
        updater.start_polling()
        logger.info("✅ Bot is running with new improvements!")
        updater.idle()
        
    except Exception as e:
        logger.error(f"❌ Bot startup error: {e}")

if __name__ == '__main__':
    main()
