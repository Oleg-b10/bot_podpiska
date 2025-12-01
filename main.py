import asyncio
from bot.core.loader import dp, bot
from config.features import *

# === ВСЕ МОДУЛИ ===
from bot.modules.main_menu.handlers import router as menu_router
if ENABLE_FAQ:
    from bot.modules.faq.handlers import router as faq_router
from bot.modules.lead_capture.handlers import router as lead_router

# === АДМИНКА + РАССЫЛКИ ===
if ENABLE_ADMIN_PANEL:
    from bot.modules.admin.handlers import router as admin_router
    dp.include_router(admin_router)

# === ПОДКЛЮЧАЕМ РОУТЕРЫ ===
dp.include_router(menu_router)
if ENABLE_FAQ:
    dp.include_router(faq_router)
dp.include_router(lead_router)
# feedback_router больше НЕ НУЖЕН — вся поддержка теперь в main_menu

# === БАЗА И ПЛАНИРОВЩИК ===
from database.models import create_tables

if ENABLE_ADMIN_PANEL:
    try:
        from bot.modules.mailing.scheduler import start_scheduler
    except ImportError:
        print("scheduler.py не найден")

async def main():
    print("Бот-подписка 2025 — финальная версия без оплаты")
    await create_tables()

    if ENABLE_ADMIN_PANEL:
        try:
            start_scheduler()
            print("Рассылки активны")
        except:
            pass

    print("Запущено успешно:")
    print("   • Главное меню")
    if ENABLE_FAQ: print("   • FAQ")
    print("   • Заявки → Google Sheets")
    print("   • Техподдержка → топики (в main_menu)")
    if ENABLE_ADMIN_PANEL: print("   • Админ-панель + рассылки")
    print("   Оплата отключена в features.py")

    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())