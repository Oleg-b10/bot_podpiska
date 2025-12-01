import asyncio
from bot.core.loader import dp, bot
from config.features import *
from database.models import create_tables

# РОУТЕРЫ В ПРАВИЛЬНОМ ПОРЯДКЕ
from bot.modules.main_menu.handlers import router as menu_router
from bot.modules.support.handlers import router as support_router
from bot.modules.lead_capture.handlers import router as lead_router

dp.include_router(menu_router)      # 1. меню и кнопки
dp.include_router(support_router)   # 2. поддержка
dp.include_router(lead_router)      # 3. заявка — последней!

# Остальные модули (рефералка, оплата и т.д.)
from bot.modules.referral.handlers import router as referral_router
dp.include_router(referral_router)

if ENABLE_PAYMENT:
    try:
        from bot.modules.payments import payments_router
        dp.include_router(payments_router)
    except Exception as e:
        print(f"Оплата не подключена: {e}")

if ENABLE_ADMIN_PANEL:
    from bot.modules.admin.handlers import router as admin_router
    dp.include_router(admin_router)

async def main():
    print("Запуск бота...")
    await create_tables()
    print("Бот запущен — КАНОНИЧНЫЙ РЕЖИМ 2025")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
