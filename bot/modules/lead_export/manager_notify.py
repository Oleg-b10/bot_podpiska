from bot.core.loader import bot
from config.settings import MANAGER_ID

async def notify_manager(data: dict):
    text = f"""НОВАЯ ЗАЯВКА!

Имя: {data['name']}
Телефон: {data['phone']}
E-mail: {data['email']}
Username: @{data.get('username','Нет')}
ID: {data['user_id']}"""
    try:
        await bot.send_message(MANAGER_ID, text)
    except: pass
