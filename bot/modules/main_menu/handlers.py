# bot/modules/main_menu/handlers.py — РАБОЧАЯ ВЕРСИЯ 2025
from aiogram import Router, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardRemove
from database.models import async_session, User
from datetime import datetime
from sqlalchemy import select

router = Router(name="main_menu")

# Главное меню — 2 инлайн-кнопки
def get_start_kb():
    kb = [
        [InlineKeyboardButton(text="FAQ", callback_data="show_faq")],
        [InlineKeyboardButton(text="Оставить заявку", callback_data="start_lead")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=kb)

@router.message(F.text == "/start")
async def cmd_start(message: Message):
    await message.answer(
        "Привет! Я бот-подписка для экспертов\n\nЧто тебя интересует?",
        reply_markup=get_start_kb()
    )

# ОБНОВЛЕНИЕ АКТИВНОСТИ ПРИ ЛЮБОМ СООБЩЕНИИ
@router.message()
async def update_activity(message: Message):
    async with async_session() as session:
        result = await session.execute(select(User).where(User.user_id == message.from_user.id))
        user = result.scalar_one_or_none()
        
        if not user:
            # Если пользователя нет — создаём
            new_user = User(
                user_id=message.from_user.id,
                username=message.from_user.username,
                first_name=message.from_user.first_name,
                joined_at=datetime.utcnow(),
                last_active=datetime.utcnow(),
                is_lead=False,
                is_paid=False
            )
            session.add(new_user)
        else:
            # Если есть — обновляем last_active
            user.last_active = datetime.utcnow()
        
        await session.commit()