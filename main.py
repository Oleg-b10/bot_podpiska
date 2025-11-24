import asyncio
from bot.core.loader import dp, bot
from bot.modules.lead_capture.handlers import router as lead_router
from config.features import ENABLE_ADMIN_PANEL

# Лиды (у тебя уже были)
dp.include_router(lead_router)

# Админка + рассылки (если включены)
if ENABLE_ADMIN_PANEL:
    from bot.modules.admin.handlers import router as admin_router
    dp.include_router(admin_router)
    from bot.modules.mailing.scheduler import start_scheduler  # запускаем APScheduler

# Создаём таблицы + запускаем
from database.models import create_tables

async def main():
    await create_tables()
    if ENABLE_ADMIN_PANEL:
        start_scheduler()
    print("Бот запущен — лиды + рассылки + админка")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())