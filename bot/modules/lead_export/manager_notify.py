from aiogram import Bot
from config.settings import MANAGER_ID  # ← твой ID из .env

async def notify_manager(data: dict):
    try:
        from bot.core.loader import bot
        text = (
            f"НОВАЯ ЗАЯВКА!\n\n"
            f"Имя: {data['name']}\n"
            f"Телефон: {data['phone']}\n"
            f"E-mail: {data['email'] or 'не указан'}\n"
            f"ID: {data['user_id']}\n"
            f"Username: @{data['username']}"
        )
        await bot.send_message(MANAGER_ID, text)
    except Exception as e:
        print("Не удалось отправить менеджеру:", e)
