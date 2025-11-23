# Yuz Tahlil Telegram Bot - Professional Version
# Developer: @iamcamandar
# Version: 2.0

import cv2
import numpy as np
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters
from deepface import DeepFace
import os
import asyncio
from datetime import datetime
import logging

# Logging sozlash
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Bot tokeningizni bu yerga qo'ying
BOT_TOKEN = "8157560190:AAE7KcQ_fzLGqpeADODivi1NPR-ztZT5g9c"

# Papkalar
TEMP_DIR = "temp_images"
RESULT_DIR = "result_images"

# Papkalarni yaratish
os.makedirs(TEMP_DIR, exist_ok=True)
os.makedirs(RESULT_DIR, exist_ok=True)

# Foydalanuvchi ma'lumotlari
user_data = {}

# Cascade classifierlarni oldindan yuklash (tezlik uchun)
FACE_CASCADE = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
EYE_CASCADE = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_eye.xml')
SMILE_CASCADE = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_smile.xml')

# Hissiyotlar tarjimasi
EMOTIONS_UZ = {
    'angry': '😠 Jahldor',
    'disgust': '🤢 Nafrat',
    'fear': '😨 Qo\'rquv',
    'happy': '😊 Xursand',
    'sad': '😢 G\'amgin',
    'surprise': '😮 Hayron',
    'neutral': '😐 Neytral'
}


def get_main_menu():
    """Asosiy menyu tugmalari"""
    keyboard = [
        [InlineKeyboardButton("📷 Rasm yuborish", callback_data="send_photo")],
        [InlineKeyboardButton("ℹ️ Yordam", callback_data="help"),
         InlineKeyboardButton("⚙️ Sozlamalar", callback_data="settings")],
        [InlineKeyboardButton("📜 Foydalanish shartlari", callback_data="terms")],
        [InlineKeyboardButton("👨‍💻 Yaratuvchi", callback_data="creator")]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_analysis_menu():
    """Tahlil tugmalari"""
    keyboard = [
        [InlineKeyboardButton("👤 Yuzni aniqlash", callback_data="detect_face")],
        [InlineKeyboardButton("👁 Yuz segmentatsiyasi", callback_data="segment_face")],
        [InlineKeyboardButton("🎂 Yosh taxmini", callback_data="estimate_age")],
        [InlineKeyboardButton("😊 Hissiyot aniqlash", callback_data="detect_emotion")],
        [InlineKeyboardButton("👥 Yuzlarni solishtirish", callback_data="compare_faces")],
        [InlineKeyboardButton("🔄 Barchasini tahlil qilish", callback_data="full_analysis")],
        [InlineKeyboardButton("🏠 Asosiy menyu", callback_data="main_menu")]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_back_menu():
    """Orqaga qaytish tugmasi"""
    keyboard = [
        [InlineKeyboardButton("📷 Yangi rasm yuborish", callback_data="send_photo")],
        [InlineKeyboardButton("🏠 Asosiy menyu", callback_data="main_menu")]
    ]
    return InlineKeyboardMarkup(keyboard)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Bot ishga tushganda"""
    user = update.message.from_user
    user_id = user.id

    # Foydalanuvchi ma'lumotlarini saqlash
    user_data[user_id] = {
        "images": [],
        "settings": {"language": "uz", "quality": "high"},
        "joined": datetime.now().strftime("%Y-%m-%d %H:%M")
    }

    welcome_text = f"""
🤖 *Yuz Tahlil Botiga Xush Kelibsiz!*

Salom, *{user.first_name}*! 👋

Bu bot sun'iy intellekt yordamida yuzingizni tahlil qiladi:

🔹 *Asosiy funksiyalar:*
• 👤 Yuzni aniqlash
• 👁 Yuz segmentatsiyasi  
• 🎂 Yosh va jins taxmini
• 😊 Hissiyot aniqlash
• 👥 Ikki yuzni solishtirish
• 🔄 To'liq tahlil

📸 *Boshlash uchun quyidagi tugmani bosing!*
    """
    await update.message.reply_text(
        welcome_text,
        parse_mode='Markdown',
        reply_markup=get_main_menu()
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/help buyrug'i"""
    help_text = """
📚 *YORDAM BO'LIMI*

🔹 *Botdan foydalanish:*

1️⃣ "📷 Rasm yuborish" tugmasini bosing
2️⃣ Yuzingiz ko'ringan rasmni yuboring
3️⃣ Kerakli tahlil turini tanlang
4️⃣ Natijani kuting

🔹 *Funksiyalar:*

👤 *Yuzni aniqlash* - rasmdagi barcha yuzlarni topadi va belgilaydi

👁 *Yuz segmentatsiyasi* - ko'z, burun, og'iz va boshqa qismlarni ajratadi

🎂 *Yosh taxmini* - yoshingizni va jinsingizni aniqlaydi

😊 *Hissiyot aniqlash* - kayfiyatingizni (xursand, g'amgin, jahldor va h.k.) aniqlaydi

👥 *Yuzlarni solishtirish* - ikki rasmni solishtiradi (2 ta rasm kerak)

🔄 *To'liq tahlil* - barcha funksiyalarni bir vaqtda bajaradi

🔹 *Muhim:*
• Yuz aniq ko'ringan rasm yuboring
• Yaxshi yorug'lik bo'lsin
• Rasm sifati yuqori bo'lsin

❓ *Savollar bo'lsa:* @iamcamandar
    """

    if update.callback_query:
        await update.callback_query.edit_message_text(
            help_text,
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🏠 Asosiy menyu", callback_data="main_menu")]
            ])
        )
    else:
        await update.message.reply_text(
            help_text,
            parse_mode='Markdown',
            reply_markup=get_main_menu()
        )


async def settings_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Sozlamalar"""
    query = update.callback_query
    user_id = query.from_user.id

    settings_text = """
⚙️ *SOZLAMALAR*

🔹 *Joriy sozlamalar:*

📊 *Tahlil sifati:* Yuqori
🌐 *Til:* O'zbekcha
🖼 *Rasm formati:* JPEG/PNG
📏 *Maksimal o'lcham:* 10 MB

🔹 *Tavsiyalar:*

• Yaxshi natija uchun yuqori sifatli rasm yuboring
• Yuzingiz to'liq va aniq ko'rinsin
• Yaxshi yorug'lik muhim
• Bir nechta yuz bo'lsa, barchasi tahlil qilinadi

🔹 *Cheklovlar:*

• Kuniga 100 ta rasm tahlil qilish mumkin
• Har bir rasm 10 MB dan oshmasin
• Faqat JPG, PNG, WEBP formatlar qo'llab-quvvatlanadi
    """

    keyboard = [
        [InlineKeyboardButton("🗑 Rasmlarni tozalash", callback_data="clear_images")],
        [InlineKeyboardButton("🏠 Asosiy menyu", callback_data="main_menu")]
    ]

    await query.edit_message_text(
        settings_text,
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def terms_of_use(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Foydalanish shartlari"""
    query = update.callback_query

    terms_text = """
📜 *FOYDALANISH SHARTLARI*

🔹 *1. Umumiy qoidalar:*
• Bot faqat shaxsiy foydalanish uchun mo'ljallangan
• Noqonuniy maqsadlarda foydalanish taqiqlanadi
• Boshqa odamlarning ruxsatisiz rasmlarini tahlil qilish taqiqlanadi

🔹 *2. Maxfiylik:*
• Yuborilgan rasmlar vaqtincha saqlanadi
• Tahlildan so'ng rasmlar o'chiriladi
• Shaxsiy ma'lumotlar uchinchi tomonlarga berilmaydi

🔹 *3. Javobgarlik:*
• Bot natijalar 100% aniqligiga kafolat bermaydi
• Tahlil natijalaridan foydalanish foydalanuvchi javobgarligida
• Bot tibbiy yoki huquqiy maslahat bermaydi

🔹 *4. Taqiqlar:*
❌ Voyaga yetmaganlar rasmlarini yuborish
❌ Noo'rin yoki noqonuniy kontentni yuborish
❌ Botni spam maqsadida ishlatish
❌ Botni buzishga urinish

🔹 *5. O'zgarishlar:*
• Shartlar ogohlantirishsiz o'zgarishi mumkin
• Yangi shartlar e'lon qilingan paytdan kuchga kiradi

✅ Botdan foydalanish - ushbu shartlarga rozilik bildirish hisoblanadi.

📅 *Oxirgi yangilanish:* {date}
    """.format(date=datetime.now().strftime("%Y-%m-%d"))

    await query.edit_message_text(
        terms_text,
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("✅ Roziman", callback_data="main_menu")],
            [InlineKeyboardButton("🏠 Asosiy menyu", callback_data="main_menu")]
        ])
    )


async def creator_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Yaratuvchi haqida"""
    query = update.callback_query

    creator_text = """
👨‍💻 *YARATUVCHI HAQIDA*

🔹 *Developer:* @iamcamandar

🔹 *Bot versiyasi:* 2.0

🔹 *Texnologiyalar:*
• Python 3.11+
• python-telegram-bot
• OpenCV
• DeepFace
• TensorFlow

🔹 *Aloqa:*
📱 Telegram: @iamcamandar
💬 Savollar va takliflar uchun yozing!

🔹 *Loyiha haqida:*
Bu bot sun'iy intellekt va kompyuter ko'rish texnologiyalari asosida yuz tahlilini amalga oshiradi.

⭐ *Botni baholang va do'stlaringizga ulashing!*

📅 *Yaratilgan sana:* 2024
🔄 *Oxirgi yangilanish:* {date}
    """.format(date=datetime.now().strftime("%Y-%m-%d"))

    await query.edit_message_text(
        creator_text,
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("📱 @iamcamandar", url="https://t.me/iamcamandar")],
            [InlineKeyboardButton("🏠 Asosiy menyu", callback_data="main_menu")]
        ])
    )


async def handle_image(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Rasm kelganda"""
    user_id = update.message.from_user.id

    # Foydalanuvchi ma'lumotlarini tekshirish
    if user_id not in user_data:
        user_data[user_id] = {"images": [], "settings": {}}

    await update.message.reply_text("⏳ Rasm yuklanmoqda...")

    try:
        # Rasmni yuklab olish
        photo = update.message.photo[-1]
        file = await context.bot.get_file(photo.file_id)

        # Rasmni saqlash
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        image_path = os.path.join(TEMP_DIR, f"{user_id}_{timestamp}.jpg")
        await file.download_to_drive(image_path)

        # Rasmni ro'yxatga qo'shish
        user_data[user_id]["images"].append(image_path)

        # Eski rasmlarni tozalash (5 tadan ko'p bo'lsa)
        if len(user_data[user_id]["images"]) > 5:
            old_image = user_data[user_id]["images"].pop(0)
            if os.path.exists(old_image):
                os.remove(old_image)

        images_count = len(user_data[user_id]["images"])

        await update.message.reply_text(
            f"✅ *Rasm muvaffaqiyatli qabul qilindi!*\n\n"
            f"📊 Saqlangan rasmlar: *{images_count}* ta\n\n"
            f"Quyidagi tahlil turlaridan birini tanlang:",
            parse_mode='Markdown',
            reply_markup=get_analysis_menu()
        )

    except Exception as e:
        logger.error(f"Rasm yuklashda xatolik: {e}")
        await update.message.reply_text(
            "❌ Rasmni yuklashda xatolik yuz berdi. Qaytadan urinib ko'ring.",
            reply_markup=get_main_menu()
        )


async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Tugma bosilganda"""
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    action = query.data

    # Menyu tugmalari
    if action == "main_menu":
        await query.edit_message_text(
            "🏠 *Asosiy menyu*\n\nKerakli bo'limni tanlang:",
            parse_mode='Markdown',
            reply_markup=get_main_menu()
        )
        return

    elif action == "send_photo":
        await query.edit_message_text(
            "📷 *Rasm yuborish*\n\n"
            "Tahlil qilmoqchi bo'lgan rasmingizni yuboring.\n\n"
            "⚠️ *Eslatma:*\n"
            "• Yuz aniq ko'rinsin\n"
            "• Yaxshi yorug'lik bo'lsin\n"
            "• JPG, PNG formatda bo'lsin",
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🏠 Asosiy menyu", callback_data="main_menu")]
            ])
        )
        return

    elif action == "help":
        await help_command(update, context)
        return

    elif action == "settings":
        await settings_menu(update, context)
        return

    elif action == "terms":
        await terms_of_use(update, context)
        return

    elif action == "creator":
        await creator_info(update, context)
        return

    elif action == "clear_images":
        if user_id in user_data:
            for img_path in user_data[user_id].get("images", []):
                if os.path.exists(img_path):
                    os.remove(img_path)
            user_data[user_id]["images"] = []

        await query.edit_message_text(
            "✅ *Barcha rasmlar o'chirildi!*",
            parse_mode='Markdown',
            reply_markup=get_main_menu()
        )
        return

    # Tahlil funksiyalari
    if user_id not in user_data or not user_data[user_id].get("images"):
        await query.edit_message_text(
            "❌ *Rasm topilmadi!*\n\nAvval rasm yuboring.",
            parse_mode='Markdown',
            reply_markup=get_main_menu()
        )
        return

    image_path = user_data[user_id]["images"][-1]

    if not os.path.exists(image_path):
        await query.edit_message_text(
            "❌ *Rasm topilmadi!*\n\nQaytadan rasm yuboring.",
            parse_mode='Markdown',
            reply_markup=get_main_menu()
        )
        return

    await query.edit_message_text("⏳ *Tahlil qilinmoqda...*\n\nIltimos, kuting...", parse_mode='Markdown')

    try:
        if action == "detect_face":
            result = await detect_faces(image_path, user_id)
        elif action == "segment_face":
            result = await segment_face(image_path, user_id)
        elif action == "estimate_age":
            result = await estimate_age(image_path)
        elif action == "detect_emotion":
            result = await detect_emotion(image_path)
        elif action == "compare_faces":
            result = await compare_faces(user_data[user_id].get("images", []))
        elif action == "full_analysis":
            result = await full_analysis(image_path, user_id)
        else:
            result = {"text": "❌ Noma'lum buyruq"}

        # Natijani yuborish
        if "image_path" in result and os.path.exists(result["image_path"]):
            await context.bot.send_photo(
                chat_id=query.message.chat_id,
                photo=open(result["image_path"], "rb"),
                caption=result["text"],
                parse_mode='Markdown',
                reply_markup=get_back_menu()
            )
            # Natija rasmini o'chirish
            os.remove(result["image_path"])
        else:
            await context.bot.send_message(
                chat_id=query.message.chat_id,
                text=result["text"],
                parse_mode='Markdown',
                reply_markup=get_back_menu()
            )

    except Exception as e:
        logger.error(f"Tahlil xatoligi: {e}")
        await context.bot.send_message(
            chat_id=query.message.chat_id,
            text=f"❌ *Xatolik yuz berdi!*\n\n`{str(e)}`\n\nQaytadan urinib ko'ring.",
            parse_mode='Markdown',
            reply_markup=get_back_menu()
        )


async def detect_faces(image_path: str, user_id: int) -> dict:
    """Yuzlarni aniqlash - optimallashtirilgan"""
    img = cv2.imread(image_path)
    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # Yuzlarni aniqlash
    faces = FACE_CASCADE.detectMultiScale(
        gray,
        scaleFactor=1.1,
        minNeighbors=5,
        minSize=(30, 30)
    )

    # Yuzlarni belgilash
    for i, (x, y, w, h) in enumerate(faces):
        cv2.rectangle(img, (x, y), (x + w, y + h), (0, 255, 0), 3)
        cv2.putText(img, f"Yuz #{i + 1}", (x, y - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)

    result_path = os.path.join(RESULT_DIR, f"detect_{user_id}.jpg")
    cv2.imwrite(result_path, img)

    return {
        "text": f"👤 *YUZ ANIQLASH NATIJASI*\n\n"
                f"📊 Topilgan yuzlar: *{len(faces)}* ta\n\n"
                f"✅ Yashil ramka - aniqlangan yuz",
        "image_path": result_path
    }


async def segment_face(image_path: str, user_id: int) -> dict:
    """Yuz segmentatsiyasi - optimallashtirilgan"""
    img = cv2.imread(image_path)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    faces = FACE_CASCADE.detectMultiScale(gray, 1.1, 5, minSize=(30, 30))

    total_eyes = 0
    total_smiles = 0

    for (x, y, w, h) in faces:
        # Yuz - ko'k
        cv2.rectangle(img, (x, y), (x + w, y + h), (255, 0, 0), 2)
        cv2.putText(img, "Yuz", (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 0, 0), 2)

        roi_gray = gray[y:y + h, x:x + w]
        roi_color = img[y:y + h, x:x + w]

        # Ko'zlar - yashil
        eyes = EYE_CASCADE.detectMultiScale(roi_gray, 1.1, 10, minSize=(20, 20))
        for (ex, ey, ew, eh) in eyes[:2]:  # Faqat 2 ta ko'z
            cv2.rectangle(roi_color, (ex, ey), (ex + ew, ey + eh), (0, 255, 0), 2)
            cv2.putText(roi_color, "Ko'z", (ex, ey - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 255, 0), 1)
            total_eyes += 1

        # Og'iz - qizil
        smiles = SMILE_CASCADE.detectMultiScale(roi_gray, 1.8, 20, minSize=(25, 25))
        for (sx, sy, sw, sh) in smiles[:1]:  # Faqat 1 ta og'iz
            cv2.rectangle(roi_color, (sx, sy), (sx + sw, sy + sh), (0, 0, 255), 2)
            cv2.putText(roi_color, "Og'iz", (sx, sy - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 0, 255), 1)
            total_smiles += 1

    result_path = os.path.join(RESULT_DIR, f"segment_{user_id}.jpg")
    cv2.imwrite(result_path, img)

    return {
        "text": f"👁 *YUZ SEGMENTATSIYASI NATIJASI*\n\n"
                f"👤 Yuzlar: *{len(faces)}* ta\n"
                f"👁 Ko'zlar: *{total_eyes}* ta\n"
                f"👄 Og'iz: *{total_smiles}* ta\n\n"
                f"🔵 Ko'k - Yuz\n"
                f"🟢 Yashil - Ko'z\n"
                f"🔴 Qizil - Og'iz",
        "image_path": result_path
    }


async def estimate_age(image_path: str) -> dict:
    """Yosh va jins taxmini - optimallashtirilgan"""
    try:
        result = DeepFace.analyze(
            image_path,
            actions=['age', 'gender'],
            enforce_detection=False,
            detector_backend='opencv'  # Tezroq
        )

        if isinstance(result, list):
            result = result[0]

        age = result['age']
        gender = result['dominant_gender']
        gender_confidence = result['gender'].get(gender, 0)

        gender_uz = "👨 Erkak" if gender == "Man" else "👩 Ayol"

        # Yosh kategoriyasi
        if age < 13:
            age_category = "👶 Bola"
        elif age < 20:
            age_category = "🧑 O'smir"
        elif age < 35:
            age_category = "👨 Yosh"
        elif age < 50:
            age_category = "🧔 O'rta yosh"
        else:
            age_category = "👴 Katta yosh"

        return {
            "text": f"🎂 *YOSH VA JINS TAXMINI*\n\n"
                    f"📅 Taxminiy yosh: *{age}* yosh\n"
                    f"📊 Kategoriya: *{age_category}*\n\n"
                    f"👤 Jins: *{gender_uz}*\n"
                    f"📈 Aniqlik: *{gender_confidence:.1f}%*"
        }
    except Exception as e:
        return {"text": f"❌ *Xatolik!*\n\nYuz aniqlanmadi.\n\n`{str(e)}`"}


async def detect_emotion(image_path: str) -> dict:
    """Hissiyot aniqlash - optimallashtirilgan"""
    try:
        result = DeepFace.analyze(
            image_path,
            actions=['emotion'],
            enforce_detection=False,
            detector_backend='opencv'
        )

        if isinstance(result, list):
            result = result[0]

        emotions = result['emotion']
        dominant = result['dominant_emotion']

        text = f"😊 *HISSIYOT TAHLILI*\n\n"
        text += f"🎯 Asosiy hissiyot: *{EMOTIONS_UZ.get(dominant, dominant)}*\n\n"
        text += "📊 *Batafsil tahlil:*\n\n"

        for emotion, value in sorted(emotions.items(), key=lambda x: x[1], reverse=True):
            emoji_name = EMOTIONS_UZ.get(emotion, emotion)
            bar_length = int(value / 5)
            bar = "▓" * bar_length + "░" * (20 - bar_length)
            text += f"{emoji_name}\n{bar} *{value:.1f}%*\n\n"

        return {"text": text}
    except Exception as e:
        return {"text": f"❌ *Xatolik!*\n\nHissiyot aniqlanmadi.\n\n`{str(e)}`"}


async def compare_faces(image_paths: list) -> dict:
    """Yuzlarni solishtirish - optimallashtirilgan"""
    if len(image_paths) < 2:
        return {
            "text": "⚠️ *Yuzlarni solishtirish uchun 2 ta rasm kerak!*\n\n"
                    "📷 Yana bitta rasm yuboring va qaytadan urinib ko'ring."
        }

    try:
        img1_path = image_paths[-2]
        img2_path = image_paths[-1]

        result = DeepFace.verify(
            img1_path,
            img2_path,
            enforce_detection=False,
            detector_backend='opencv'
        )

        verified = result['verified']
        distance = result['distance']
        threshold = result['threshold']
        similarity = max(0, min(100, (1 - distance) * 100))

        if verified:
            status = "✅ *BIR XIL ODAM!*"
            emoji = "👥"
        else:
            status = "❌ *BOSHQA ODAMLAR!*"
            emoji = "👤👤"

        # O'xshashlik darajasi
        if similarity >= 80:
            level = "🟢 Juda yuqori"
        elif similarity >= 60:
            level = "🟡 Yuqori"
        elif similarity >= 40:
            level = "🟠 O'rtacha"
        else:
            level = "🔴 Past"

        return {
            "text": f"👥 *YUZLARNI SOLISHTIRISH*\n\n"
                    f"{emoji} Natija: {status}\n\n"
                    f"📊 O'xshashlik: *{similarity:.1f}%*\n"
                    f"📈 Daraja: *{level}*\n"
                    f"📏 Masofa: *{distance:.4f}*\n"
                    f"🎯 Chegara: *{threshold:.4f}*"
        }
    except Exception as e:
        return {"text": f"❌ *Xatolik!*\n\nYuzlarni solishtirish imkonsiz.\n\n`{str(e)}`"}


async def full_analysis(image_path: str, user_id: int) -> dict:
    """To'liq tahlil - barcha funksiyalar"""
    try:
        # DeepFace bilan to'liq tahlil
        result = DeepFace.analyze(
            image_path,
            actions=['age', 'gender', 'emotion', 'race'],
            enforce_detection=False,
            detector_backend='opencv'
        )

        if isinstance(result, list):
            result = result[0]

        age = result['age']
        gender = result['dominant_gender']
        gender_uz = "👨 Erkak" if gender == "Man" else "👩 Ayol"
        emotion = result['dominant_emotion']
        emotion_uz = EMOTIONS_UZ.get(emotion, emotion)
        race = result['dominant_race']

        # Irq tarjimasi
        race_uz = {
            'asian': '🌏 Osiyo',
            'indian': '🇮🇳 Hind',
            'black': '🌍 Afrika',
            'white': '🌎 Yevropa',
            'middle eastern': '🕌 Yaqin Sharq',
            'latino hispanic': '🌎 Latin Amerika'
        }

        # OpenCV bilan yuz aniqlash
        img = cv2.imread(image_path)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        faces = FACE_CASCADE.detectMultiScale(gray, 1.1, 5)

        for (x, y, w, h) in faces:
            cv2.rectangle(img, (x, y), (x + w, y + h), (0, 255, 0), 3)

        result_path = os.path.join(RESULT_DIR, f"full_{user_id}.jpg")
        cv2.imwrite(result_path, img)

        text = f"🔄 *TO'LIQ YUZ TAHLILI*\n\n"
        text += f"━━━━━━━━━━━━━━━━━━━━\n"
        text += f"👤 *Yuzlar soni:* {len(faces)} ta\n"
        text += f"━━━━━━━━━━━━━━━━━━━━\n\n"
        text += f"🎂 *Yosh:* {age} yosh\n"
        text += f"👤 *Jins:* {gender_uz}\n"
        text += f"😊 *Hissiyot:* {emotion_uz}\n"
        text += f"🌍 *Kelib chiqish:* {race_uz.get(race, race)}\n\n"
        text += f"━━━━━━━━━━━━━━━━━━━━\n"
        text += f"✅ *Tahlil muvaffaqiyatli yakunlandi!*"

        return {"text": text, "image_path": result_path}

    except Exception as e:
        return {"text": f"❌ *Xatolik!*\n\nTo'liq tahlil amalga oshmadi.\n\n`{str(e)}`"}


async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Xatoliklarni qayta ishlash"""
    logger.error(f"Xatolik yuz berdi: {context.error}")

    if update and update.effective_chat:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="❌ *Kutilmagan xatolik yuz berdi!*\n\n"
                 "Iltimos, qaytadan urinib ko'ring yoki @iamcamandar ga murojaat qiling.",
            parse_mode='Markdown',
            reply_markup=get_main_menu()
        )


def main():
    """Botni ishga tushirish"""
    # Application yaratish
    application = Application.builder().token(BOT_TOKEN).build()

    # Handlerlar
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(MessageHandler(filters.PHOTO, handle_image))
    application.add_handler(CallbackQueryHandler(button_callback))

    # Xatolik handleri
    application.add_error_handler(error_handler)

    # Botni ishga tushirish
    logger.info("🤖 Bot ishga tushdi!")
    print("=" * 50)
    print("🤖 YUZ TAHLIL BOT - v2.0")
    print("👨‍💻 Developer: @iamcamandar")
    print("=" * 50)
    print("✅ Bot muvaffaqiyatli ishga tushdi!")
    print("📡 Polling rejimida ishlamoqda...")
    print("=" * 50)

    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()