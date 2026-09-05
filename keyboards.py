from aiogram.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    ReplyKeyboardMarkup,
    KeyboardButton
)

def main_menu_keyboard() -> ReplyKeyboardMarkup:
    kb = [
        [KeyboardButton(text="🎯 Testni boshlash")],
        [KeyboardButton(text="📊 Mening statistikam"), KeyboardButton(text="🏆 Reyting")],
        [KeyboardButton(text="🔄 Xatolar ustida ishlash"), KeyboardButton(text="ℹ️ Bot haqida")]
    ]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

def collection_select_keyboard() -> InlineKeyboardMarkup:
    kb = [
        [InlineKeyboardButton(text="📘 1-To'plam (309 ta savol)", callback_data="coll_1")],
        [InlineKeyboardButton(text="📗 2-To'plam (386 ta savol)", callback_data="coll_2")],
        [InlineKeyboardButton(text="🔀 Barcha savollar (695 ta)", callback_data="coll_3")],
        [InlineKeyboardButton(text="📂 Bo'limlar bo'yicha", callback_data="coll_cats")],
        [InlineKeyboardButton(text="❌ Bekor qilish", callback_data="cancel_quiz")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=kb)

def question_count_keyboard(collection_id: int) -> InlineKeyboardMarkup:
    kb = [
        [
            InlineKeyboardButton(text="10 ta", callback_data=f"cnt_{collection_id}_10"),
            InlineKeyboardButton(text="20 ta", callback_data=f"cnt_{collection_id}_20"),
            InlineKeyboardButton(text="30 ta", callback_data=f"cnt_{collection_id}_30")
        ],
        [
            InlineKeyboardButton(text="50 ta", callback_data=f"cnt_{collection_id}_50"),
            InlineKeyboardButton(text="Barchasi (To'liq)", callback_data=f"cnt_{collection_id}_all")
        ],
        [InlineKeyboardButton(text="⬅️ Orqaga", callback_data="back_to_coll")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=kb)

def categories_keyboard(collection_id: int, categories: dict) -> InlineKeyboardMarkup:
    kb = []
    for idx, (cat_name, q_list) in enumerate(categories.items()):
        short_name = cat_name[:35] + ("..." if len(cat_name) > 35 else "")
        kb.append([InlineKeyboardButton(text=f"📌 {short_name} ({len(q_list)})", callback_data=f"cat_{collection_id}_{idx}")])
    kb.append([InlineKeyboardButton(text="⬅️ Orqaga", callback_data="back_to_coll")])
    return InlineKeyboardMarkup(inline_keyboard=kb)

def answer_options_keyboard(options_count: int) -> InlineKeyboardMarkup:
    letters = ["A", "B", "C", "D", "E", "F"][:options_count]
    row = []
    for idx, l in enumerate(letters):
        row.append(InlineKeyboardButton(text=f"🔘 {l}", callback_data=f"ans_{idx}"))
    
    # 2 or 4 buttons per row
    rows = []
    if len(row) <= 3:
        rows.append(row)
    elif len(row) == 4:
        rows.append(row[:2])
        rows.append(row[2:])
    else:
        rows.append(row[:3])
        rows.append(row[3:])
        
    rows.append([InlineKeyboardButton(text="🛑 Testni to'xtatish", callback_data="stop_quiz")])
    return InlineKeyboardMarkup(inline_keyboard=rows)

def next_question_keyboard() -> InlineKeyboardMarkup:
    kb = [
        [InlineKeyboardButton(text="➡️ Keyingi savol", callback_data="next_q")],
        [InlineKeyboardButton(text="🛑 Testni to'xtatish", callback_data="stop_quiz")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=kb)

def result_keyboard(has_mistakes: bool = False) -> InlineKeyboardMarkup:
    kb = []
    if has_mistakes:
        kb.append([InlineKeyboardButton(text="🔄 Xatolar ustida ishlash", callback_data="retry_mistakes")])
    kb.append([InlineKeyboardButton(text="🔁 Qayta topshirish", callback_data="restart_quiz")])
    kb.append([InlineKeyboardButton(text="🏠 Bosh menyu", callback_data="to_main_menu")])
    return InlineKeyboardMarkup(inline_keyboard=kb)
