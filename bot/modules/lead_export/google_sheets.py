import gspread
from datetime import datetime

def append_to_sheet(data: dict) -> bool:
    try:
        gc = gspread.service_account(filename="credentials.json")
        sh = gc.open_by_key("1ATlPHcQqgvrnhIVOIfZv1Pw6-1TzBkF4ZJF3QMEBKZs")
        ws = sh.sheet1
        row = [datetime.now().strftime("%d.%m.%Y %H:%M"), data["name"], data["phone"], data["email"], data["user_id"], data.get("username","")]
        ws.append_row(row)
        return True
    except Exception as e:
        print("Sheets error:", e)
        return False
