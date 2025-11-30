# bot/modules/referral/handlers.py — 100% РАБОЧИЙ КОД 2025 (с правильным select!)
from aiogram import Router, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from config.features import ADMIN_IDS
from database.models import async_session, User
from bot.core.loader import bot
from datetime import datetime
from sqlalchemy import select  # ← ЭТО ВАЖНО!

router = Router()

@router.message(Command("referral"))
async def cmd_referral(message: Message):
    user_id = message.from_user.id
    async with async_session() as session:
        result = await session.execute(select(User).where(User.user_id == user_id))
        user = result.scalar_one_or_none()
        
        if not user:
            await message.answer("Ты ещё не зарегистрирован.")
            return

        bot_username = (await bot.get_me()).username
        ref_link = f"https://t.me/{bot_username}?start=ref{user_id}"
        
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Пригласить друга", url=ref_link)],
        ])
        
        text = f""" ТВОЯ РЕФЕРАЛЬНАЯ ССЫЛКА

{ref_link}

Ты пригласил: <b>{user.referral_count}</b> чел.
Бонусные дни: <b>{user.referral_bonus_days}</b>

За каждого друга — +3 дня доступа тебе
Другу — скидка 10% на первый тариф"""

        await message.answer(text, reply_markup=kb, disable_web_page_preview=True)

# === ОБРАБОТКА РЕФЕРАЛЬНОЙ ССЫЛКИ ===
@router.message(F.text.startswith("/start ref"))
async def referral_start(message: Message):
    try:
        referrer_id = int(message.text.split("ref")[1].strip())
    except:
        referrer_id = None

    if referrer_id == message.from_user.id:
        await message.answer("Нельзя приглашать самого себя 😅")
        return

    async with async_session() as session:
        result = await session.execute(select(User).where(User.user_id == message.from_user.id))
        user = result.scalar_one_or_none()
        
        was_new_referral = False
        
        if not user:
            user = User(
                user_id=message.from_user.id,
                username=message.from_user.username,
                first_name=message.from_user.first_name,
                joined_at=datetime.utcnow(),
                last_active=datetime.utcnow(),
                referrer_id=referrer_id,
                referral_bonus_days=0,
                referral_count=0,
                is_lead=False,
                is_paid=False
            )
            session.add(user)
            was_new_referral = True
        else:
            if user.referrer_id is None and referrer_id:
                user.referrer_id = referrer_id
                was_new_referral = True
            user.last_active = datetime.utcnow()

        if was_new_referral and referrer_id:
            result = await session.execute(select(User).where(User.user_id == referrer_id))
            referrer = result.scalar_one_or_none()
            if referrer:
                referrer.referral_count += 1
                referrer.referral_bonus_days += 3
                await bot.send_message(
                    referrer_id,
                    "Ура! По твоей ссылке пришёл новый пользователь!\n+3 дня доступа тебе начислено 🎉"
                )

        await session.commit()

    if was_new_referral:
        await message.answer("Добро пожаловать! Ты пришёл по реферальной ссылке — скидка 10% на первый тариф!")
    else:
        await message.answer("С возвращением!")