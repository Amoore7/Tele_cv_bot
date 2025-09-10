import os
import logging
import re
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler
from docx import Document

# تمكين التسجيل
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# مراحل المحادثة
NAME, PHONE, EMAIL, EDUCATION, EXPERIENCE, SKILLS_HELP, SKILLS, LANGUAGES, PAYMENT = range(9)

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

# مهارات حسب التخصص (عربي للمستخدم، إنجليزي للسيرة)
SKILLS_BY_FIELD = {
    "تكنولوجيا": {
        "عربي": [
            "برمجة بايثون", "تطوير الويب", "قواعد البيانات", 
            "الشبكات", "الأمن السيبراني", "تعلم الآلة",
            "تحليل البيانات", "تطوير التطبيقات", "إدارة الخوادم"
        ],
        "انجليزي": [
            "Python Programming", "Web Development", "Database Management", 
            "Networking", "Cybersecurity", "Machine Learning",
            "Data Analysis", "App Development", "Server Administration"
        ]
    },
    "هندسة": {
        "عربي": [
            "تصميم أنظمة", "إدارة المشاريع", "الرسم الهندسي",
            "تحليل الهياكل", "الصيانة والتشغيل", "ضبط الجودة",
            "التخطيط والتصميم", "إعداد التقارير الفنية", "إدارة الفريق"
        ],
        "انجليزي": [
            "System Design", "Project Management", "Technical Drawing",
            "Structural Analysis", "Maintenance & Operations", "Quality Control",
            "Planning & Design", "Technical Reporting", "Team Management"
        ]
    },
    "محاسبة": {
        "عربي": [
            "إعداد القوائم المالية", "المحاسبة الضريبية", "مراجعة الحسابات",
            "الميزانيات والتخطيط", "برامج المحاسبة", "التحليل المالي",
            "التقارير المالية", "مراقبة التكاليف", "المحاسبة الإدارية"
        ],
        "انجليزي": [
            "Financial Statements Preparation", "Tax Accounting", "Auditing",
            "Budgeting & Planning", "Accounting Software", "Financial Analysis",
            "Financial Reporting", "Cost Control", "Managerial Accounting"
        ]
    },
    "تسويق": {
        "عربي": [
            "التسويق الرقمي", "إدارة وسائل التواصل", "تحليل السوق",
            "إعداد الحملات الإعلانية", "تحليل المنافسين", "إدارة العلامة التجارية",
            "بحوث التسويق", "التسويق بالمحتوى", "تحسين محركات البحث"
        ],
        "انجليزي": [
            "Digital Marketing", "Social Media Management", "Market Analysis",
            "Advertising Campaigns", "Competitor Analysis", "Brand Management",
            "Market Research", "Content Marketing", "SEO Optimization"
        ]
    },
    "تعليم": {
        "عربي": [
            "التخطيط للدروس", "إدارة الصف", "تقويم الطلاب",
            "التعليم التفاعلي", "التعليم عن بعد", "تصميم المناهج",
            "التوجيه والإرشاد", "التعليم الخاص", "استخدام التقنية في التعليم"
        ],
        "انجليزي": [
            "Lesson Planning", "Classroom Management", "Student Assessment",
            "Interactive Teaching", "Distance Learning", "Curriculum Design",
            "Guidance & Counseling", "Special Education", "Technology Integration"
        ]
    },
    "طب": {
        "عربي": [
            "التشخيص الطبي", "الرعاية الصحية", "الإسعافات الأولية",
            "إدارة المستشفيات", "البحث الطبي", "التعامل مع المرضى",
            "استخدام الأجهزة الطبية", "السجلات الطبية", "الصحة العامة"
        ],
        "انجليزي": [
            "Medical Diagnosis", "Healthcare", "First Aid",
            "Hospital Management", "Medical Research", "Patient Care",
            "Medical Equipment Usage", "Medical Records", "Public Health"
        ]
    },
    "أخرى": {
        "عربي": [
            "القيادة", "التواصل الفعال", "إدارة الوقت",
            "حل المشكلات", "العمل الجماعي", "الإبداع والابتكار",
            "التخطيط الاستراتيجي", "التفاوض", "خدمة العملاء"
        ],
        "انجليزي": [
            "Leadership", "Effective Communication", "Time Management",
            "Problem Solving", "Teamwork", "Creativity & Innovation",
            "Strategic Planning", "Negotiation", "Customer Service"
        ]
    }
}

# دالة للتحقق من صحة الإيميل
def is_valid_email(email):
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    # رسالة الترحيب التلقائية
    welcome_message = (
        "👋 **مرحباً بك في بوت إنشاء السيرة الذاتية الاحترافية!**\n\n"
        "🎯 **ماذا يمكنني أن أفعل لك؟**\n"
        "• إنشاء سيرة ذاتية إنجليزية احترافية\n"
        "• تنسيق متوافق مع أنظمة التوظيف العالمية (ATS)\n"
        "• مساعدتك في كتابة المهارات المناسبة\n"
        "• إنشاء ملف Word جاهز للتحميل\n\n"
        "💡 **للبدء، أرسل /start أو اكتب 'ابدأ'**\n\n"
        "⚡ **للتوقف في أي وقت، أرسل /cancel**"
    )
    
    await update.message.reply_text(welcome_message)
    
    # إذا كان المستخدم كتب /start نبدأ العملية
    if update.message.text == '/start':
        start_message = (
            "🚀 **لنبدأ إنشاء سيرتك الذاتية!**\n\n"
            "📝 **ملاحظة مهمة:** السيرة الذاتية سيتم إنشاؤها باللغة الإنجليزية "
            "لتوافقها مع أنظمة التوظيف العالمية (ATS).\n\n"
            "أدخل اسمك بالكامل:"
        )
        await update.message.reply_text(start_message)
        return NAME
    
    return ConversationHandler.END

async def get_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_data['name'] = update.message.text
    await update.message.reply_text("شكرًا! الآن أدخل رقم جوالك:")
    return PHONE

async def get_phone(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_data['phone'] = update.message.text
    await update.message.reply_text("أدخل بريدك الإلكتروني (مثال: name@example.com):")
    return EMAIL

async def get_email(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    email = update.message.text.strip()
    
    # التحقق من صحة الإيميل
    if not is_valid_email(email):
        await update.message.reply_text(
            "❌ البريد الإلكتروني غير صحيح. يرجى إدخال بريد إلكتروني صالح (مثال: name@example.com):"
        )
        return EMAIL  # البقاء في نفس المرحلة
    
    user_data['email'] = email
    await update.message.reply_text("أدخل مؤهلاتك التعليمية:")
    return EDUCATION

async def get_education(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_data['education'] = update.message.text
    await update.message.reply_text("أدخل خبراتك العملية:")
    return EXPERIENCE

async def get_experience(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_data['experience'] = update.message.text
    
    # سؤال عن المساعدة في المهارات
    keyboard = [['نعم', 'لا']]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)
    await update.message.reply_text(
        "هل تريد مساعدة في اقتراح المهارات المناسبة لسيرتك الذاتية؟",
        reply_markup=reply_markup
    )
    return SKILLS_HELP

async def skills_help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    response = update.message.text.lower()
    
    if response == 'نعم':
        # عرض قائمة التخصصات
        fields_keyboard = [[field] for field in SKILLS_BY_FIELD.keys()]
        reply_markup = ReplyKeyboardMarkup(fields_keyboard, one_time_keyboard=True)
        await update.message.reply_text(
            "اختر تخصصك الرئيسي:",
            reply_markup=reply_markup
        )
        return SKILLS
    else:
        await update.message.reply_text(
            "حسنًا، أدخل مهاراتك (افصل بينها بفواصل):",
            reply_markup=ReplyKeyboardRemove()
        )
        return LANGUAGES

async def get_skills(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_input = update.message.text
    
    # إذا اختار تخصصًا من القائمة
    if user_input in SKILLS_BY_FIELD:
        skills_arabic = SKILLS_BY_FIELD[user_input]["عربي"]
        skills_english = SKILLS_BY_FIELD[user_input]["انجليزي"]
        
        # حفظ المهارات بالإنجليزية للسي في
        user_data['skills_english'] = skills_english
        
        # عرض المهارات بالعربي للمستخدم
        skills_text = "\n".join([f"• {skill}" for skill in skills_arabic])
        
        await update.message.reply_text(
            f"📋 **مهارات مقترحة لتخصص {user_input}:**\n\n{skills_text}\n\n"
            "أدخل المهارات التي تنطبق عليك (افصل بينها بفواصل):",
            reply_markup=ReplyKeyboardRemove()
        )
        return LANGUAGES
    else:
        # إذا أدخل المهارات مباشرة
        user_data['skills_english'] = update.message.text
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
    
    # المهارات (بالإنجليزية)
    doc.add_heading('Skills', level=1)
    skills_text = data.get('skills_english', 'No skills provided')
    if isinstance(skills_text, list):
        skills_text = ", ".join(skills_text)
    doc.add_paragraph(skills_text)
    
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
    
    # إضافة handler للرسالة التلقائية
    application.add_handler(CommandHandler("start", start))
    
    # محادثة
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('ابدأ', start)],
        states={
            NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_name)],
            PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_phone)],
            EMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_email)],
            EDUCATION: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_education)],
            EXPERIENCE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_experience)],
            SKILLS_HELP: [MessageHandler(filters.TEXT & ~filters.COMMAND, skills_help)],
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
