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
dp.include_router(lead_router)

async def main():
    print("Бот запущен!")
    print(f"FAQ: {'ВКЛЮЧЁН' if ENABLE_FAQ else 'ВЫКЛЮЧЕН'}")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
