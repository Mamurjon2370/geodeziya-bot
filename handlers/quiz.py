import time
import os
from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery, FSInputFile
from quiz_manager import quiz_manager
from database import (
    save_quiz_result,
    save_user_mistake,
    remove_user_mistake,
    get_user_mistakes,
    sessions
)
from keyboards import (
    collection_select_keyboard,
    question_count_keyboard,
    categories_keyboard,
    answer_options_keyboard,
    next_question_keyboard,
    result_keyboard
)

router = Router()

letters = ["A", "B", "C", "D", "E", "F", "G", "H"]

def format_question_text(q_obj, current_num, total_count, coll_name):
    q_text = q_obj["question"]
    opts = q_obj["options"]
    
    text = f"❓ <b>Savol {current_num}/{total_count}</b> [<i>{coll_name}</i>]\n"
    if q_obj.get("category") and q_obj["category"] != "Umumiy savollar":
        text += f"📂 <i>{q_obj['category']}</i>\n"
    text += f"\n<b>{q_text}</b>\n\n"
    
    for idx, opt in enumerate(opts):
        l = letters[idx] if idx < len(letters) else f"{idx+1}"
        text += f"<b>{l})</b> {opt}\n"
        
    return text

async def send_current_question(bot: Bot, chat_id: int, user_id: int):
    sess = sessions.get(user_id)
    if not sess:
        return
        
    q_idx = sess["current_idx"]
    questions = sess["questions"]
    
    if q_idx >= len(questions):
        await finish_quiz(bot, chat_id, user_id)
        return
        
    q_obj = questions[q_idx]
    sess["answered"] = False
    sessions.sync(user_id)
    
    total_q = len(questions)
    coll_name = sess["collection_name"]
    text = format_question_text(q_obj, q_idx + 1, total_q, coll_name)
    reply_kb = answer_options_keyboard(len(q_obj["options"]))
    
    image_path = q_obj.get("image")
    sent = False
    if image_path and os.path.exists(image_path):
        try:
            photo = FSInputFile(image_path)
            if len(text) <= 1024:
                await bot.send_photo(chat_id=chat_id, photo=photo, caption=text, reply_markup=reply_kb, parse_mode="HTML")
            else:
                await bot.send_photo(chat_id=chat_id, photo=photo)
                await bot.send_message(chat_id=chat_id, text=text, reply_markup=reply_kb, parse_mode="HTML")
            sent = True
        except Exception as e:
            print(f"Error sending photo {image_path}: {e}")
            sent = False
            
    if not sent:
        await bot.send_message(chat_id=chat_id, text=text, reply_markup=reply_kb, parse_mode="HTML")

async def finish_quiz(bot: Bot, chat_id: int, user_id: int):
    sess = sessions.get(user_id)
    if not sess:
        return
        
    total_q = len(sess["questions"])
    correct = sess["correct_count"]
    mistakes = total_q - correct
    duration = int(time.time() - sess["start_time"])
    minutes = duration // 60
    seconds = duration % 60
    
    percentage = round((correct / total_q) * 100, 1) if total_q > 0 else 0
    
    if percentage >= 86:
        grade = "🏆 A'lo (5 baho)"
    elif percentage >= 71:
        grade = "👍 Yaxshi (4 baho)"
    elif percentage >= 55:
        grade = "👌 Qoniqarli (3 baho)"
    else:
        grade = "⚠️ Qoniqarsiz (2 baho)"
        
    if not sess["is_mistakes_mode"]:
        save_quiz_result(
            user_id=user_id,
            category=sess["collection_name"],
            total_q=total_q,
            correct_q=correct,
            duration_sec=duration
        )
        
    result_text = (
        f"🏁 <b>Test muvaffaqiyatli yakunlandi!</b>\n\n"
        f"📚 <b>Bo'lim:</b> {sess['collection_name']}\n"
        f"⏱ <b>Sarflangan vaqt:</b> {minutes:02d}:{seconds:02d}\n"
        f"📊 <b>Natija:</b> {correct} / {total_q} ({percentage}%)\n"
        f"🎯 <b>Baho:</b> {grade}\n"
        f"❌ <b>Xatolar soni:</b> {mistakes} ta\n\n"
    )
    
    if mistakes > 0:
        result_text += "💡 <i>Xato qilgan savollaringizni qayta yechish uchun quyidagi tugmadan foydalanishingiz mumkin:</i>"
    else:
        result_text += "🎉 <i>Barcha savollarga 100% to'g'ri javob berdingiz! Tabriklaymiz!</i>"
        
    kb = result_keyboard(has_mistakes=(mistakes > 0 or len(sess["mistakes_made"]) > 0))
    await bot.send_message(chat_id=chat_id, text=result_text, reply_markup=kb, parse_mode="HTML")
    
    # Keep session around only if user wants to restart or review
    # but reset status

@router.message(F.text == "🎯 Testni boshlash")
async def start_quiz_menu(message: Message):
    text = (
        "🎯 <b>Test to'plamini tanlang:</b>\n\n"
        "🔹 <b>1-To'plam</b> — 309 ta rasmiy test savoli\n"
        "🔹 <b>2-To'plam</b> — 386 ta kengaytirilgan test savoli\n"
        "🔹 <b>Barcha savollar</b> — 695 ta aralash test savollari\n"
        "🔹 <b>Bo'limlar bo'yicha</b> — Alohida mavzular bo'yicha test"
    )
    await message.answer(text, reply_markup=collection_select_keyboard(), parse_mode="HTML")

@router.callback_query(F.data.in_(["coll_1", "coll_2", "coll_3"]))
async def select_count(callback: CallbackQuery):
    coll_id = int(callback.data.split("_")[1])
    names = {1: "1-To'plam", 2: "2-To'plam", 3: "Barcha savollar (1 & 2)"}
    
    text = (
        f"📚 <b>Tanlangan: {names[coll_id]}</b>\n\n"
        f"Nechta savol yechmoqchisiz? Quyidagilardan birini tanlang:"
    )
    await callback.message.edit_text(text, reply_markup=question_count_keyboard(coll_id), parse_mode="HTML")

@router.callback_query(F.data == "coll_cats")
async def select_category_collection(callback: CallbackQuery):
    # Combine categories
    all_cats = dict(quiz_manager.categories_1)
    all_cats.update(quiz_manager.categories_2)
    
    text = "📂 <b>Mavzuni (bo'limni) tanlang:</b>"
    await callback.message.edit_text(text, reply_markup=categories_keyboard(3, all_cats), parse_mode="HTML")

@router.callback_query(F.data.startswith("cat_"))
async def start_category_quiz(callback: CallbackQuery, bot: Bot):
    parts = callback.data.split("_")
    coll_id = int(parts[1])
    cat_idx = int(parts[2])
    
    all_cats = list(quiz_manager.categories_1.items()) + list(quiz_manager.categories_2.items())
    if cat_idx < len(all_cats):
        cat_name = all_cats[cat_idx][0]
    else:
        cat_name = "Umumiy"
        
    questions = quiz_manager.get_questions(collection_id=coll_id, count=None, shuffle=True, category=cat_name)
    if not questions:
        await callback.answer("Ushbu bo'limda savollar topilmadi.", show_alert=True)
        return
        
    user_id = callback.from_user.id
    sessions[user_id] = {
        "questions": questions,
        "current_idx": 0,
        "correct_count": 0,
        "start_time": time.time(),
        "collection_name": cat_name[:30],
        "mistakes_made": [],
        "is_mistakes_mode": False,
        "answered": False
    }
    
    await callback.message.delete()
    await send_current_question(bot, callback.message.chat.id, user_id)

@router.callback_query(F.data.startswith("cnt_"))
async def start_quiz_with_count(callback: CallbackQuery, bot: Bot):
    parts = callback.data.split("_")
    coll_id = int(parts[1])
    count_str = parts[2]
    count = None if count_str == "all" else int(count_str)
    
    names = {1: "1-To'plam", 2: "2-To'plam", 3: "Umumiy test"}
    coll_name = names.get(coll_id, "Test")
    
    questions = quiz_manager.get_questions(collection_id=coll_id, count=count, shuffle=True)
    if not questions:
        await callback.answer("Savollar yuklanmadi.", show_alert=True)
        return
        
    user_id = callback.from_user.id
    sessions[user_id] = {
        "questions": questions,
        "current_idx": 0,
        "correct_count": 0,
        "start_time": time.time(),
        "collection_name": coll_name,
        "mistakes_made": [],
        "is_mistakes_mode": False,
        "answered": False
    }
    
    await callback.message.delete()
    await send_current_question(bot, callback.message.chat.id, user_id)

@router.callback_query(F.data.startswith("ans_"))
async def handle_answer(callback: CallbackQuery, bot: Bot):
    user_id = callback.from_user.id
    sess = sessions.get(user_id)
    
    if not sess:
        await callback.answer("Sessiya topilmadi. Qaytadan boshlang.", show_alert=True)
        return
        
    if sess["answered"]:
        await callback.answer("Siz allaqachon javob berdingiz!", show_alert=False)
        return
        
    sess["answered"] = True
    ans_idx = int(callback.data.split("_")[1])
    q_obj = sess["questions"][sess["current_idx"]]
    
    is_correct = (ans_idx == q_obj["correct_option_index"])
    correct_letter = letters[q_obj["correct_option_index"]] if q_obj["correct_option_index"] < len(letters) else "?"
    correct_text = q_obj["options"][q_obj["correct_option_index"]]
    
    user_letter = letters[ans_idx] if ans_idx < len(letters) else f"{ans_idx+1}"
    
    if is_correct:
        sess["correct_count"] += 1
        # If in mistakes mode, remove from user mistakes DB
        remove_user_mistake(user_id, q_obj.get("collection_id", 1), q_obj["id"])
        response_badge = f"✅ <b>To'g'ri javob! ({user_letter})</b>"
    else:
        sess["mistakes_made"].append(q_obj)
        save_user_mistake(user_id, q_obj.get("collection_id", 1), q_obj["id"])
        response_badge = (
            f"❌ <b>Noto'g'ri! (Siz tanladingiz: {user_letter})</b>\n"
            f"✅ <b>To'g'ri javob: {correct_letter}) {correct_text}</b>"
        )
        
    # Notify user with alert banner & update inline keyboard with Next button
    total_q = len(sess["questions"])
    curr_q = sess["current_idx"] + 1
    sessions.sync(user_id)
    
    status_text = (
        f"{response_badge}\n\n"
        f"📊 <i>Hozirgi holat: {sess['correct_count']}/{curr_q} ta to'g'ri</i>"
    )
    
    # We edit or reply with feedback
    await callback.message.reply(status_text, reply_markup=next_question_keyboard(), parse_mode="HTML")
    await callback.answer("Qabul qilindi!")

@router.callback_query(F.data == "next_q")
async def next_question(callback: CallbackQuery, bot: Bot):
    user_id = callback.from_user.id
    sess = sessions.get(user_id)
    if not sess:
        await callback.answer("Sessiya tugagan.", show_alert=True)
        return
        
    sess["current_idx"] += 1
    sessions.sync(user_id)
    await callback.message.delete()
    await send_current_question(bot, callback.message.chat.id, user_id)

@router.message(F.text == "🔄 Xatolar ustida ishlash")
async def mistakes_work(message: Message, bot: Bot):
    user_id = message.from_user.id
    mistakes = get_user_mistakes(user_id)
    
    if not mistakes:
        await message.answer(
            "🎉 <b>Ajoyib! Sizda xatolar bazasida hech qanday savol yo'q.</b>\n\n"
            "Yangi testlarni topshirish orqali bilimlaringizni sinab ko'ring!",
            parse_mode="HTML"
        )
        return
        
    # Prepare question objects
    q_objs = []
    for coll_id, q_id in mistakes:
        q = quiz_manager.get_question_by_id(coll_id, q_id)
        if q:
            q_objs.append({
                "collection_id": coll_id,
                "id": q["id"],
                "category": q.get("category", "Xatolar"),
                "question": q["question"],
                "image": q["image"],
                "options": list(q["options"]),
                "correct_option_index": q["correct_option_index"],
                "correct_answer": q["correct_answer"]
            })
            
    if not q_objs:
        await message.answer("Xatolar topilmadi.", parse_mode="HTML")
        return
        
    sessions[user_id] = {
        "questions": q_objs,
        "current_idx": 0,
        "correct_count": 0,
        "start_time": time.time(),
        "collection_name": "🔄 Xatolar ustida ishlash",
        "mistakes_made": [],
        "is_mistakes_mode": True,
        "answered": False
    }
    
    await message.answer(
        f"🔄 <b>Xatolar ustida ishlash boshlandi!</b>\n"
        f"📝 Jami xato qilingan savollar soni: <b>{len(q_objs)} ta</b>\n\n"
        f"Har bir to'g'ri javob bergan savolingiz xatolar ro'yxatidan avtomatik o'chiriladi!",
        parse_mode="HTML"
    )
    await send_current_question(bot, message.chat.id, user_id)

@router.callback_query(F.data == "retry_mistakes")
async def callback_retry_mistakes(callback: CallbackQuery, bot: Bot):
    await callback.message.delete()
    await mistakes_work(callback.message, bot)

@router.callback_query(F.data == "restart_quiz")
async def callback_restart_quiz(callback: CallbackQuery, bot: Bot):
    await callback.message.delete()
    await start_quiz_menu(callback.message)

@router.callback_query(F.data == "to_main_menu")
async def callback_to_main(callback: CallbackQuery):
    await callback.message.delete()
    await callback.message.answer("🏠 <b>Bosh menyu:</b>", reply_markup=collection_select_keyboard(), parse_mode="HTML")

@router.callback_query(F.data == "back_to_coll")
async def callback_back_to_coll(callback: CallbackQuery):
    await start_quiz_menu(callback.message)

@router.callback_query(F.data.in_(["cancel_quiz", "stop_quiz"]))
async def cancel_quiz_handler(callback: CallbackQuery):
    user_id = callback.from_user.id
    if user_id in sessions:
        del sessions[user_id]
    await callback.message.delete()
    await callback.message.answer("🛑 <b>Test to'xtatildi.</b>", parse_mode="HTML")
