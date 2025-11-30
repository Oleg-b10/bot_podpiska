import requests
from config.settings import GSHEET_URL

def append_to_sheet(data: dict) -> bool:
    """
    Отправляет лид в Google Apps Script (bound script в таблице клиента)
    Возвращает True — если записано успешно
    """
    if not GSHEET_URL:
        print("GSHEET_URL не указан в .env")
        return False

    payload = {
        "name": data.get("name", "").strip(),
        "phone": data.get("phone", "").strip(),
        "email": data.get("email", "").strip(),
        "user_id": str(data.get("user_id", "")),
        "username": data.get("username", "Нет").replace("@", "")
    }

    try:
        # Важно: headers и timeout
        response = requests.post(
            url=GSHEET_URL,
            json=payload,
            timeout=15,
            headers={"Content-Type": "application/json"}
        )

        # Google Apps Script возвращает "OK" как plain text
        if response.status_code == 200 and response.text.strip() == "OK":
            return True
        else:
            print(f"Apps Script вернул: {response.status_code} | {response.text}")
            return False

    except requests.exceptions.RequestException as e:
        print(f"Ошибка сети при отправке в таблицу: {e}")
        return False
    except Exception as e:
        print(f"Неизвестная ошибка: {e}")
        return False