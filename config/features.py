# ═════════════════════════════════════════
# КОНСТРУКТОР БОТА — включай/выключай что угодно
# ═════════════════════════════════════════

import os
from dotenv import load_dotenv
load_dotenv()  # ← читаем .env

# === ВКЛЮЧЕНИЕ МОДУЛЕЙ ===
ENABLE_LEAD_FORM       = True
ENABLE_LEAD_EXPORT     = True
ENABLE_MANAGER_NOTIFY  = True

ENABLE_FAQ             = True
ENABLE_AUTOFUNNEL      = False
ENABLE_ADMIN_PANEL     = True      # ← ВКЛЮЧАЕМ АДМИНКУ И РАССЫЛКИ
ENABLE_PAYMENT         = True
ENABLE_STATISTICS      = False

# === АДМИНЫ И МЕНЕДЖЕР (читаем из .env) ===
ADMIN_IDS = [int(x.strip()) for x in os.getenv("ADMIN_IDS", "").split(",") if x.strip().isdigit()]
MANAGER_ID = int(os.getenv("MANAGER_ID", "0")) if os.getenv("MANAGER_ID") else None

# === ТЕКСТЫ ===
WELCOME_TEXT = "Привет! Оставь заявку на доступ \n\nКак тебя зовут?"
SUCCESS_TEXT = "Готово! Заявка принята \nМенеджер свяжется в ближайшее время!"

# === БАЗА ДАННЫХ ===
DATABASE_URL = "postgresql+asyncpg://postgres:root@localhost:5432/bottest"

# === GSHEET (если через Apps Script) ===
GSHEET_WEB_APP_URL = os.getenv("GSHEET_URL")  # ← твоя ссылка из .env

