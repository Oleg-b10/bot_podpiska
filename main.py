import asyncio
from bot.core.loader import dp, bot
from bot.modules.lead_capture.handlers import router as lead_router
dp.include_router(lead_router)

async def main():
    print("Бот запущен — сбор лидов активен!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
