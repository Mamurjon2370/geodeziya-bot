from aiogram import Router, F
from aiogram.types import Message
from database import get_user_stats, get_leaderboard

router = Router()

@router.message(F.text == "📊 Mening statistikam")
async def show_my_stats(message: Message):
    user_id = message.from_user.id
    stats = get_user_stats(user_id)
    
    if not stats or stats['tests_count'] == 0:
        await message.answer(
            "📊 <b>Siz hali birorta ham test topshirmagansiz.</b>\n\n"
            "«🎯 Testni boshlash» tugmasini bosib birinchi testingizni boshlang!",
            parse_mode="HTML"
        )
        return
        
    text = (
        f"📊 <b>Sizning shaxsiy statistikangiz:</b>\n\n"
        f"👤 <b>Foydalanuvchi:</b> {stats['name']}\n"
        f"📝 <b>Topshirilgan testlar soni:</b> {stats['tests_count']} ta\n"
        f"✅ <b>To'g'ri topilgan savollar:</b> {stats['total_score']} ta\n"
        f"❓ <b>Jami yechilgan savollar:</b> {stats['total_questions']} ta\n"
        f"📈 <b>Umumiy aniqlik:</b> {stats['accuracy']}%\n"
        f"❌ <b>Xatolar bazasidagi savollar:</b> {stats['mistakes_count']} ta\n\n"
        f"💡 <i>Xatolaringizni to'g'rilash uchun «🔄 Xatolar ustida ishlash» bo'limiga kiring.</i>"
    )
    await message.answer(text, parse_mode="HTML")

@router.message(F.text == "🏆 Reyting")
async def show_leaderboard(message: Message):
    leaders = get_leaderboard(limit=10)
    
    if not leaders:
        await message.answer("🏆 <b>Hozircha reyting jadvali bo'sh.</b>\nBirinchi bo'lib test yeching va reytingda peshqadam bo'ling!", parse_mode="HTML")
        return
        
    text = "🏆 <b>Eng yuqori natija ko'rsatgan 10 ta foydalanuvchi:</b>\n\n"
    medals = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]
    
    for idx, (name, score, total_q, tests) in enumerate(leaders):
        acc = round((score / total_q) * 100, 1) if total_q > 0 else 0
        medal = medals[idx] if idx < len(medals) else f"{idx+1}."
        text += f"{medal} <b>{name}</b> — <b>{score} ball</b> ({acc}% aniqlik, {tests} ta test)\n"
        
    text += "\n🚀 <i>Siz ham ko'proq test yechib peshqadamlar safiga qo'shiling!</i>"
    await message.answer(text, parse_mode="HTML")
