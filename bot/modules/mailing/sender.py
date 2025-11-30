# bot/modules/mailing/sender.py — ФИНАЛЬНЫЙ РАБОЧИЙ КОД 2025 (с сегментацией + без ошибок)
import asyncio
import random
from sqlalchemy import select, or_
from database.models import async_session, User, Mailing
from bot.core.loader import bot
from aiogram import types
from datetime import datetime, timedelta
import os
import aiofiles

# Простая замена {{ name }} без Jinja2
async def render_template(template_name: str, variables: dict) -> str:
    template_path = f"bot/modules/mailing/templates/{template_name}.txt"
    if not os.path.exists(template_path):
        return "Шаблон не найден"
    try:
        async with aiofiles.open(template_path, "r", encoding="utf-8") as f:
            content = await f.read()
        text = content
        for key, value in variables.items():
            text = text.replace(f"{{{{ {key} }}}}", str(value))
            text = text.replace(f"{{ {key} }}", str(value))
        return text
    except Exception as e:
        print(f"Ошибка шаблона: {e}")
        return "Ошибка чтения шаблона"

# === ОСНОВНАЯ ФУНКЦИЯ РАССЫЛКИ С ПОДДЕРЖКОЙ СЕГМЕНТАЦИИ ===
async def run_mailing(mailing_id: int):
    async with async_session() as session:
        mailing = await session.get(Mailing, mailing_id)
        if not mailing or mailing.status != "draft":
            return

        # Получаем сегменты из базы (поле segments в Mailing)
        segments = mailing.segments or ["all"]

        # Формируем запрос по сегментам
        query = select(User.user_id)
        if "all" not in segments:
            conditions = []
            today = datetime.utcnow().date()
            week_ago = today - timedelta(days=7)
            month_ago = today - timedelta(days=30)

            if "leads" in segments:
                conditions.append(User.is_lead == True)
            if "paid" in segments:
                conditions.append(User.is_paid == True)
            if "active7" in segments:
                conditions.append(User.last_active >= week_ago)
            if "active30" in segments:
                conditions.append(User.last_active >= month_ago)
            if "inactive" in segments:
                conditions.append(User.last_active < month_ago)

            if conditions:
                query = query.where(or_(*conditions))

        # Получаем только ID пользователей
        user_ids = (await session.execute(query)).scalars().all()

        mailing.status = "running"
        await session.commit()

        sent = delivered = 0
        for user_id in user_ids:  # ← теперь user_id — это int!
            try:
                # Формируем текст
                if mailing.template and mailing.template != "manual":
                    # Нужно получить имя пользователя
                    result = await session.execute(select(User).where(User.user_id == user_id))
                    user = result.scalar_one_or_none()
                    name = user.first_name or "Друг" if user else "Друг"
                    text = await render_template(mailing.template, {"name": name})
                else:
                    text = mailing.text or "Привет!"

                # Кнопка
                kb = None
                if mailing.button_text:
                    url = mailing.button_url or ""
                    if url.startswith("@"):
                        url = "https://t.me/" + url[1:]
                    kb = types.InlineKeyboardMarkup(inline_keyboard=[[
                        types.InlineKeyboardButton(text=mailing.button_text, url=url)
                    ]])

                # Отправка
                if mailing.photo:
                    await bot.send_photo(user_id, mailing.photo, caption=text, reply_markup=kb)
                else:
                    await bot.send_message(user_id, text, reply_markup=kb, disable_web_page_preview=True)
                
                delivered += 1
            except Exception as e:
                print(f"Ошибка отправки пользователю {user_id}: {e}")

            sent += 1
            mailing.sent = sent
            mailing.delivered = delivered
            await session.commit()

            # Антибан 30–35 сообщений в секунду
            await asyncio.sleep(random.uniform(0.028, 0.045))

        mailing.status = "finished"
        await session.commit()