import requests
import os
from config.settings import GSHEET_URL

def append_to_sheet(data: dict) -> bool:
    if not GSHEET_URL:
        print("Ошибка: GSHEET_URL не указан")
        return False

    payload = {
        "name": data.get("name", ""),
        "phone": data.get("phone", ""),
        "email": data.get("email", ""),
        "user_id": str(data.get("user_id", "")),
        "username": data.get("username", "Нет")
    }

    try:
        r = requests.post(GSHEET_URL, json=payload, timeout=10)
        return r.text.strip() == "OK"
    except Exception as e:
        print("Ошибка отправки в Apps Script:", e)
        return False
