import asyncio
from bot.core.loader import dp, bot
from config.features import *

# === ВСЕ МОДУЛИ ===
from bot.modules.main_menu.handlers import router as menu_router          # твой старт + инлайн
from bot.modules.faq.handlers import router as faq_router                # твой FAQ
from bot.modules.lead_capture.handlers import router as lead_router      # твои заявки

# === АДМИНКА ОТ ДРУГА ===
if ENABLE_ADMIN_PANEL:
    from bot.modules.admin.handlers import router as admin_router
    dp.include_router(admin_router)

# === ПОДКЛЮЧАЕМ В ПРАВИЛЬНОМ ПОРЯДКЕ ===
dp.include_router(menu_router)    # старт и инлайн-меню
if ENABLE_FAQ:
    dp.include_router(faq_router)
dp.include_router(lead_router)    # заявки (должны быть после меню!)

# === БАЗА ДАННЫХ И ПЛАНИРОВЩИК ===
from database.models import create_tables

# Если включение планировщика рассылок (только если админка включена)
if ENABLE_ADMIN_PANEL:
    try:
        from bot.modules.mailing.scheduler import start_scheduler
    except ImportError:
        print("scheduler.py не найден — рассылки не будут работать")

async def main():
    print("Запуск бота...")
    await create_tables()  # создаём таблицы (User, Mailing и т.д.)

    # Запускаем APScheduler ТОЛЬКО ОДИН РАЗ
    if ENABLE_ADMIN_PANEL:
        try:
            start_scheduler()
            print("Планировщик рассылок запущен")
        except Exception as e:
            print(f"Не удалось запустить планировщик: {e}")

    print("Бот полностью запущен!")
    print(f"Админ-панель: {'ВКЛЮЧЕНА' if ENABLE_ADMIN_PANEL else 'ВЫКЛЮЧЕНА'}")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
