from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import CommandStart, Command
from database import register_user
from keyboards import main_menu_keyboard

router = Router()

@router.message(CommandStart())
async def cmd_start(message: Message):
    user = message.from_user
    register_user(user.id, user.full_name, user.username)
    
    welcome_text = (
        f"👋 <b>Assalomu alaykum, {user.full_name}!</b>\n\n"
        f"🎯 <b>Geodeziya, Kartografiya va Kadastr</b> fanlari bo'yicha test topshirish botiga xush kelibsiz!\n\n"
        f"📚 Bot bazasida <b>700 ga yaqin</b> rasmiy test savollari va shartli belgilar rasmlari jamlangan.\n\n"
        f"👇 Testni boshlash uchun quyidagi tugmani bosing:"
    )
    await message.answer(welcome_text, reply_markup=main_menu_keyboard(), parse_mode="HTML")

@router.message(F.text == "ℹ️ Bot haqida")
@router.message(Command("help"))
async def cmd_help(message: Message):
    help_text = (
        "ℹ️ <b>Test Sinov Boti haqida ma'lumot:</b>\n\n"
        "🔹 <b>Test bazasi:</b> 1- va 2-to'plam savol-javoblari (Geodeziya, Kartografiya, Kadastr)\n"
        "🔹 <b>Rasmli savollar:</b> Topografik shartli belgilar va sxemalar\n"
        "🔹 <b>Rejimlar:</b> 10, 20, 30, 50 yoki barcha savollarni tasodifiy tartibda yechish\n"
        "🔹 <b>Xatolar ustida ishlash:</b> Qilgan xatolaringizni alohida qayta yechish imkoni\n"
        "🔹 <b>Statistika va Reyting:</b> Ballaringiz va umumiy peshqadamlar jadvali\n\n"
        "🚀 <i>Boshlash uchun «🎯 Testni boshlash» tugmasini bosing!</i>"
    )
    await message.answer(help_text, reply_markup=main_menu_keyboard(), parse_mode="HTML")
