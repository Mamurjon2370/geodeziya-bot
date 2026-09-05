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

import config
from database import init_db
from handlers import start, stats, quiz

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("vercel_webhook")

bot = Bot(
    token=config.BOT_TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)

dp = Dispatcher()
dp.include_router(start.router)
dp.include_router(stats.router)
dp.include_router(quiz.router)

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    logger.info("Database initialized for serverless instance.")
    yield
    await bot.session.close()

app = FastAPI(title="Telegram Quiz Bot Webhook", lifespan=lifespan)

@app.get("/")
async def root():
    return {
        "status": "ok",
        "message": "Geodeziya va kartografiya Telegram bot Vercel Serverless tizimida ishlamoqda.",
        "endpoints": {
            "webhook": "/api/webhook",
            "set_webhook": "/api/set_webhook",
            "webhook_info": "/api/get_webhook_info"
        }
    }

@app.post("/")
@app.post("/api/webhook")
@app.post("/webhook")
async def handle_telegram_update(request: Request):
    try:
        data = await request.json()
        update = Update.model_validate(data, context={"bot": bot})
        await dp.feed_update(bot, update)
        return Response(status_code=status.HTTP_200_OK)
    except Exception as e:
        logger.error(f"Error handling Telegram webhook update: {e}", exc_info=True)
        return Response(status_code=status.HTTP_200_OK)

@app.get("/api/set_webhook")
async def set_webhook(url: str = None):
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
async def get_webhook_info():
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
async def delete_webhook():
    try:
        success = await bot.delete_webhook(drop_pending_updates=True)
        return {"success": success, "message": "Webhook o'chirildi."}
    except Exception as e:
        return {"success": False, "error": str(e)}
