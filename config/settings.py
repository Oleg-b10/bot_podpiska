import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")

# ADMIN_IDS и MANAGER_ID
ADMIN_IDS = [int(x.strip()) for x in os.getenv("ADMIN_IDS", "").split(",") if x.strip()]
MANAGER_ID = int(os.getenv("MANAGER_ID")) if os.getenv("MANAGER_ID") else None

# Рабочий способ через Google Apps Script
GSHEET_URL = os.getenv("GSHEET_URL")

# ID группы поддержки
SUPPORT_CHAT_ID = int(os.getenv("SUPPORT_CHAT_ID"))

# Если захочешь потом перейти на сервисный аккаунт — раскомментишь
# GSHEET_ID_CLIENT = os.getenv("GSHEET_ID_CLIENT")
# GOOGLE_CREDENTIALS = os.getenv("GOOGLE_CREDENTIALS")
