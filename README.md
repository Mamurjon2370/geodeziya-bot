# 🤖 Geodeziya va Kartografiya Test Telegram Boti

Word (`.docx`) fayllaridagi savol-javoblar va rasmli shartli belgilardan tashkil topgan zamonaviy Telegram test sinov boti.

---

## 🌟 Bot Imkoniyatlari

- 📚 **Katta savollar bazasi:** 
  - **1-To'plam:** 309 ta savol (66 ta shartli belgilar rasmi bilan)
  - **2-To'plam:** 386 ta savol (66 ta shartli belgilar rasmi bilan)
  - **Jami:** 695 ta to'liq savol-javob
- 🖼 **Rasmli savollar:** Topografik shartli belgilar rasmlari bilan to'liq integratsiya qilingan
- 🔀 **Moslashuvchan rejimlar:**
  - 10 ta, 20 ta, 30 ta, 50 ta yoki barcha savollardan test tuzish
  - Savollar va javob variantlarini tasodifiy (random) aralashtirish
  - Alohida bo'limlar/mavzular bo'yicha test topshirish
- ⚡️ **Tezkor natija va xabardorlik:** Har bir savolga javob berilganda to'g'ri/xato ekanligi darhol ko'rsatiladi
- 🔄 **Xatolar ustida ishlash:** Foydalanuvchi adashgan savollari bazada saqlanadi va ularni alohida qayta topshirish mumkin
- 📊 **Shaxsiy statistika va 🏆 Reyting:** Eng yuqori ball to'plagan foydalanuvchilar top-10 taligi
- 💾 **SQLite ma'lumotlar bazasi:** Barcha natijalar xavfsiz saqlanadi

---

## 🚀 Botni Ishga Tushirish

### 1. Telegramdan Bot Token olish
1. Telegramda [@BotFather](https://t.me/BotFather) botiga kiring.
2. `/newbot` buyrug'ini yuboring va ko'rsatmalarga asosan botingizga nom va username bering.
3. BotFather sizga taqdim etgan **HTTP API Token**ni nusxalab oling.

### 2. Tokenni `.env` fayliga yozish
`.env` faylini oching va tokenni yozing:
```env
BOT_TOKEN=1234567890:ABCdefGhIJKlmNoPQRsTUVwxyZ
ADMIN_ID=0
```

### 3. Botni ishga tushirish
Terminalda quyidagi buyruqni bering:
```bash
python bot.py
```

---

## 📁 Fayllar Strukturasi

- [bot.py](file:///f:/telegram_test/bot.py) — Botning asosiy ishga tushirish fayli
- [config.py](file:///f:/telegram_test/config.py) — Konfiguratsiya va `.env` o'quvchi
- [database.py](file:///f:/telegram_test/database.py) — SQLite ma'lumotlar bazasi (foydalanuvchilar, statistika, xatolar)
- [quiz_manager.py](file:///f:/telegram_test/quiz_manager.py) — Savollar bazasini boshqarish va test tuzish
- [keyboards.py](file:///f:/telegram_test/keyboards.py) — Barcha inline va reply menyu tugmalari
- [handlers/](file:///f:/telegram_test/handlers) — Bot logikasi (`start.py`, `quiz.py`, `stats.py`)
- [quiz_data_1.json](file:///f:/telegram_test/quiz_data_1.json) & [quiz_data_2.json](file:///f:/telegram_test/quiz_data_2.json) — Formatlangan savollar bazasi
- [media_1/](file:///f:/telegram_test/media_1) & [media_2/](file:///f:/telegram_test/media_2) — Word fayllardan ajratib olingan rasmlar
- [parse_all_questions_v3.py](file:///f:/telegram_test/parse_all_questions_v3.py) — Yangi Word fayllar yuklanganda savollarni qayta tahlil qilish skripti
