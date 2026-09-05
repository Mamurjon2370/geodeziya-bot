import os
from dotenv import load_dotenv

load_dotenv()


def _text(name: str, default: str = "") -> str:
    """Environment qiymatini oladi va ortiqcha bo'shliq/qator belgilarini kesadi.

    Vercel panelidan qiymat ko'chirib qo'yilganda oxiriga bo'sh joy yoki yangi qator
    tushib qolishi mumkin - token uchun bu "Token is invalid!" xatosini beradi.
    """
    value = os.getenv(name)
    if value is None:
        return default
    value = value.strip().strip('"').strip("'")
    return value or default


def _number(name: str, default: int = 0) -> int:
    """Bo'sh yoki noto'g'ri qiymat kelsa ham yiqilmaydi."""
    try:
        return int(_text(name, str(default)))
    except (TypeError, ValueError):
        return default


BOT_TOKEN = _text("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")
ADMIN_ID = _number("ADMIN_ID", 0)
PROXY_URL = _text("PROXY_URL", "")
WEBHOOK_URL = _text("WEBHOOK_URL", "")
WEBHOOK_PATH = _text("WEBHOOK_PATH", "/api/webhook")
