import asyncio
from bot.core.loader import dp, bot
from config.features import *

# 1. Главное меню — всегда включено
from bot.modules.main_menu.handlers import router as menu_router
dp.include_router(menu_router)

# 2. FAQ — только если включён в features
if ENABLE_FAQ:
    from bot.modules.faq.handlers import router as faq_router
    dp.include_router(faq_router)

# 3. Сбор заявки — после всех меню (важно!)
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

    print("Бот запущен!")
    print(f"FAQ: {'ВКЛЮЧЁН' if ENABLE_FAQ else 'ВЫКЛЮЧЕН'}")

    await create_tables()
    if ENABLE_ADMIN_PANEL:
        start_scheduler()
    print("Бот запущен — лиды + рассылки + админка")

    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())