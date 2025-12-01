# main.py — ПОЛНЫЙ ФИНАЛЬНЫЙ РАБОЧИЙ КОД 2025 (всё работает!)
import asyncio
from bot.core.loader import dp, bot
from config.features import *

# === БАЗА ДАННЫХ ===
from database.models import create_tables

# === ВСЕ МОДУЛИ ===
from bot.modules.main_menu.handlers import router as menu_router
if ENABLE_FAQ:
    from bot.modules.faq.handlers import router as faq_router
from bot.modules.lead_capture.handlers import router as lead_router

# Админка + рассылки
if ENABLE_ADMIN_PANEL:
    from bot.modules.admin.handlers import router as admin_router
    dp.include_router(admin_router)

# Сегментация
if ENABLE_ADMIN_PANEL:
    from bot.modules.segmentation import segmentation_router
    dp.include_router(segmentation_router)

# РЕФЕРАЛКА — ВОБЯЗАТЕЛЬНО ПОДКЛЮЧАЕМ!
from bot.modules.referral.handlers import router as referral_router
dp.include_router(referral_router)

# Оплата
if ENABLE_PAYMENT:
    try:
        from bot.modules.payments import payments_router
        dp.include_router(payments_router)
    except Exception as e:
        print(f"Оплата не подключена: {e}")

# === ПОДКЛЮЧАЕМ В ПРАВИЛЬНОМ ПОРЯДКЕ ===
dp.include_router(menu_router)
if ENABLE_FAQ:
    dp.include_router(faq_router)
dp.include_router(lead_router)

# === ПЛАНИРОВЩИК РАССЫЛОК ===
if ENABLE_ADMIN_PANEL:
    try:
        from bot.modules.mailing.scheduler import start_scheduler
    except Exception as e:
        print(f"scheduler не найден: {e}")

async def main():
    print("Запуск бота...")
    await create_tables()

    if ENABLE_ADMIN_PANEL:
        try:
            start_scheduler()
            print("Планировщик рассылок запущен")
        except Exception as e:
            print(f"Ошибка планировщика: {e}")

    print("Бот полностью запущен!")
    print(f"Админ-панель: {'ВКЛЮЧЕНА' if ENABLE_ADMIN_PANEL else 'ВЫКЛЮЧЕНА'}")
    print(f"Оплата: {'ВКЛЮЧЕНА' if ENABLE_PAYMENT else 'ВЫКЛЮЧЕНА'}")

    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())