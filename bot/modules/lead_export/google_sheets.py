import requests
from config.settings import GSHEET_URL
from datetime import datetime

def append_to_sheet(data: dict):
    try:
        payload = {
            "date": datetime.now().strftime("%d.%m.%Y %H:%M"),
            "name": data.get("name", ""),
            "phone": data.get("phone", ""),
            "email": data.get("email", "") or "не указан",
            "user_id": data.get("user_id", ""),
            "username": data.get("username", "")
        }
        response = requests.post(GSHEET_URL, json=payload, timeout=10)
        if response.status_code == 200:
            print("Лид успешно записан через Google Apps Script")
        else:
            print(f"Ошибка записи в таблицу: {response.status_code}, {response.text}")
    except Exception as e:
        print(f"Исключение при записи в Google Sheets: {e}")
