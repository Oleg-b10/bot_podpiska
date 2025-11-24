import os
from dotenv import load_dotenv
load_dotenv()

# Основные настройки
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_IDS = [int(x) for x in os.getenv("ADMIN_IDS", "").split(",") if x]
MANAGER_ID = int(os.getenv("MANAGER_ID")) if os.getenv("MANAGER_ID") else None
GSHEET_URL = os.getenv("GSHEET_URL")  # ← теперь снова есть
