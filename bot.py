import asyncio
import logging
import os
import sys
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.client.session.aiohttp import AiohttpSession

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

import config
from database import init_db
from handlers import start, stats, quiz

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

async def main():
    if not config.BOT_TOKEN or config.BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
        print("\n" + "="*60)
        print("XATOLIK: BOT_TOKEN ko'rsatilmagan!")
        print("Iltimos, .env faylini oching va Telegram bot tokeningizni yozing:")
        print("BOT_TOKEN=1234567890:ABCdefGhIJKlmNoPQRsTUVwxyZ")
        print("="*60 + "\n")
        return

    # Initialize SQLite Database
    init_db()
    logger.info("Ma'lumotlar bazasi tayyorlandi.")

    dp = Dispatcher()
    dp.include_router(start.router)
    dp.include_router(stats.router)
    dp.include_router(quiz.router)

    proxy = config.PROXY_URL or os.getenv("HTTPS_PROXY") or os.getenv("HTTP_PROXY")

    while True:
        session = AiohttpSession(proxy=proxy) if proxy else None
        if proxy:
            logger.info(f"Proxy orqali ulanmoqda: {proxy}")

        bot = Bot(
            token=config.BOT_TOKEN,
            session=session,
            default=DefaultBotProperties(parse_mode=ParseMode.HTML)
        )

        try:
            # Delete any pending webhook updates
            await bot.delete_webhook(drop_pending_updates=True)
            logger.info("Bot muvaffaqiyatli ishga tushdi va xabarlarni kutmoqda...")
            await dp.start_polling(bot)
            break
        except (KeyboardInterrupt, SystemExit):
            logger.info("Bot to'xtatildi.")
            break
        except Exception as e:
            logger.error(f"Ulanishda xatolik yuz berdi: {e}. 5 soniyadan so'ng qayta ulanishga uriniladi...")
            await asyncio.sleep(5)
        finally:
            await bot.session.close()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot to'xtatildi.")
