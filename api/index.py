import os
import sys
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, Response, status
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.types import Update

# Ensure parent directory is in sys.path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("vercel_webhook")

# Modul yuklanishida chiqqan xato Vercelda bo'sh "500 FUNCTION_INVOCATION_FAILED"
# sahifasiga aylanadi va sababi ko'rinmaydi. Shuning uchun xatoni ushlab,
# uni endpointlar orqali o'qiladigan qilib saqlaymiz.
INIT_ERROR = None
bot = None
dp = None
config = None
init_db = None

try:
    import config as _config
    from database import init_db as _init_db
    from handlers import start, stats, quiz

    config = _config
    init_db = _init_db

    bot = Bot(
        token=config.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )

    dp = Dispatcher()
    dp.include_router(start.router)
    dp.include_router(stats.router)
    dp.include_router(quiz.router)
except Exception as exc:
    INIT_ERROR = f"{type(exc).__name__}: {exc}"
    logger.error("Bot ishga tushmadi: %s", INIT_ERROR, exc_info=True)

# Vercelning ASGI runtimeida lifespan hodisasi ishga tushmasligi mumkin,
# shuning uchun bazani import paytida ham tayyorlaymiz (CREATE TABLE IF NOT EXISTS).
if init_db is not None:
    try:
        init_db()
    except Exception as exc:
        logger.error("init_db xatosi: %s", exc, exc_info=True)


@asynccontextmanager
async def lifespan(app: FastAPI):
    if init_db is not None:
        try:
            init_db()
            logger.info("Database initialized for serverless instance.")
        except Exception as exc:
            logger.error("init_db xatosi: %s", exc, exc_info=True)
    yield
    if bot is not None:
        await bot.session.close()

app = FastAPI(title="Telegram Quiz Bot Webhook", lifespan=lifespan)

@app.get("/")
async def root():
    if INIT_ERROR:
        return {
            "status": "error",
            "message": "Bot ishga tushmadi.",
            "error": INIT_ERROR,
            "hint": (
                "Token bilan bog'liq xato bo'lsa: Vercel > Settings > Environment Variables "
                "da BOT_TOKEN borligini va boshida/oxirida bo'sh joy yo'qligini tekshiring. "
                "O'zgaruvchi qo'shgandan keyin Deployments > ... > Redeploy qilish SHART."
            ),
            "diagnostika": "/api/health"
        }
    return {
        "status": "ok",
        "message": "Geodeziya va kartografiya Telegram bot Vercel Serverless tizimida ishlamoqda.",
        "endpoints": {
            "webhook": "/api/webhook",
            "set_webhook": "/api/set_webhook",
            "webhook_info": "/api/get_webhook_info",
            "health": "/api/health"
        }
    }

@app.post("/")
@app.post("/api/webhook")
@app.post("/webhook")
async def handle_telegram_update(request: Request):
    if INIT_ERROR:
        # Telegramga 200 qaytaramiz, aks holda u xabarni qayta-qayta yuboraveradi.
        logger.error("Update qabul qilindi, lekin bot ishga tushmagan: %s", INIT_ERROR)
        return Response(status_code=status.HTTP_200_OK)
    try:
        data = await request.json()
        update = Update.model_validate(data, context={"bot": bot})
        await dp.feed_update(bot, update)
        return Response(status_code=status.HTTP_200_OK)
    except Exception as e:
        logger.error(f"Error handling Telegram webhook update: {e}", exc_info=True)
        return Response(status_code=status.HTTP_200_OK)

def check_secret(secret: str):
    """
    Boshqaruv endpointlarini himoyalaydi.

    ADMIN_SECRET environment variable qo'yilmagan bo'lsa - ruxsat beriladi
    (birinchi deploy to'silib qolmasligi uchun), lekin javobda ogohlantirish chiqadi.
    Qo'yilgan bo'lsa - ?secret=... majburiy bo'ladi.
    """
    expected = os.environ.get("ADMIN_SECRET", "")
    if not expected:
        return None  # himoya yoqilmagan
    if secret != expected:
        return {
            "success": False,
            "error": "Ruxsat yo'q. To'g'ri ?secret=... qiymatini bering."
        }
    return None


def secret_warning():
    if not os.environ.get("ADMIN_SECRET"):
        return ("OGOHLANTIRISH: ADMIN_SECRET qo'yilmagan, bu endpoint ochiq. "
                "Vercel Environment Variables ga ADMIN_SECRET qo'shing.")
    return None


@app.get("/api/set_webhook")
async def set_webhook(url: str = None, secret: str = None):
    denied = check_secret(secret)
    if denied:
        return denied
    if INIT_ERROR:
        return {"success": False, "error": INIT_ERROR,
                "hint": "Avval / yoki /api/health ni oching — sabab va yechim ko'rsatilgan."}
    target_url = url or config.WEBHOOK_URL
    if not target_url:
        vercel_host = (
            os.environ.get("VERCEL_PROJECT_PRODUCTION_URL") or 
            os.environ.get("VERCEL_URL")
        )
        if vercel_host:
            target_url = f"https://{vercel_host}/api/webhook"

    if not target_url:
        return {
            "success": False,
            "error": (
                "Webhook URL aniqlanmadi. Iltimos ?url=https://loyihangiz.vercel.app/api/webhook "
                "orqali bering yoki Vercel Environment Variables ga WEBHOOK_URL qo'shing."
            )
        }

    try:
        success = await bot.set_webhook(url=target_url, drop_pending_updates=True)
        info = await bot.get_webhook_info()
        return {
            "success": success,
            "webhook_url": target_url,
            "warning": secret_warning(),
            "webhook_info": {
                "url": info.url,
                "has_custom_certificate": info.has_custom_certificate,
                "pending_update_count": info.pending_update_count,
                "last_error_message": info.last_error_message
            }
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.get("/api/get_webhook_info")
async def get_webhook_info(secret: str = None):
    denied = check_secret(secret)
    if denied:
        return denied
    if INIT_ERROR:
        return {"success": False, "error": INIT_ERROR,
                "hint": "Avval / yoki /api/health ni oching — sabab va yechim ko'rsatilgan."}
    try:
        info = await bot.get_webhook_info()
        return {
            "success": True,
            "url": info.url,
            "has_custom_certificate": info.has_custom_certificate,
            "pending_update_count": info.pending_update_count,
            "last_error_message": info.last_error_message,
            "last_error_date": str(info.last_error_date) if info.last_error_date else None
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.get("/api/delete_webhook")
async def delete_webhook(secret: str = None):
    denied = check_secret(secret)
    if denied:
        return denied
    if INIT_ERROR:
        return {"success": False, "error": INIT_ERROR,
                "hint": "Avval / yoki /api/health ni oching — sabab va yechim ko'rsatilgan."}
    try:
        success = await bot.delete_webhook(drop_pending_updates=True)
        return {"success": success, "message": "Webhook o'chirildi."}
    except Exception as e:
        return {"success": False, "error": str(e)}


@app.get("/api/health")
async def health():
    """Deploy tekshiruvi: fayllar va baza serverda joyidami?

    Bot ishga tushmagan bo'lsa ham to'liq ishlaydi - fayl va baza holatini
    tokendan alohida tekshirish uchun.
    """
    import sqlite3
    from database import get_db_path
    from quiz_manager import quiz_manager

    raw_token = os.environ.get("BOT_TOKEN", "").strip()
    report = {
        "python": sys.version.split()[0],
        "on_vercel": bool(os.environ.get("VERCEL")),
        "commit": os.environ.get("VERCEL_GIT_COMMIT_SHA", "")[:7] or None,
        "init_error": INIT_ERROR,
        "bot_token_set": bool(raw_token and raw_token != "YOUR_BOT_TOKEN_HERE"),
        # Qiymat emas, faqat holati - o'zgaruvchi umuman yetib kelganmi yoki bo'shmi.
        "bot_token_debug": {
            "env_da_bormi": "BOT_TOKEN" in os.environ,
            "uzunligi": len(raw_token),
        },
        "admin_secret_set": bool(os.environ.get("ADMIN_SECRET")),
        "questions": {
            "collection_1": quiz_manager.get_collection_count(1),
            "collection_2": quiz_manager.get_collection_count(2),
        },
    }

    # Rasm fayllari lambda ichiga tushganmi?
    all_q = quiz_manager.data_1 + quiz_manager.data_2
    with_img = [q["image"] for q in all_q if q.get("image")]
    found = sum(1 for p in with_img if os.path.exists(p))
    report["images"] = {
        "referenced": len(with_img),
        "found_on_disk": found,
        "sample": with_img[0] if with_img else None,
    }

    # Baza yozib bo'ladimi?
    db_path = get_db_path()
    try:
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM users")
        users = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM active_sessions")
        active = cur.fetchone()[0]
        conn.close()
        report["database"] = {
            "path": db_path,
            "writable": True,
            "users": users,
            "active_sessions": active,
        }
    except Exception as e:
        report["database"] = {"path": db_path, "writable": False, "error": str(e)}

    report["ok"] = (
        INIT_ERROR is None
        and report["bot_token_set"]
        and report["questions"]["collection_1"] > 0
        and report["images"]["found_on_disk"] == report["images"]["referenced"]
        and report["database"].get("writable", False)
    )
    return report
