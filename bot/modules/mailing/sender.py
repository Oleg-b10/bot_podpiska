# bot/modules/mailing/sender.py — ФИНАЛЬНЫЙ РАБОЧИЙ КОД БЕЗ ЦИКЛИЧЕСКИХ ИМПОРТОВ
import asyncio
import random
from sqlalchemy import select
from database.models import async_session, User, Mailing
from bot.core.loader import bot
from aiogram import types
import os
import aiofiles

# Функция для рендера Jinja-шаблона (встроена прямо сюда — без импортов!)
async def render_template(template_name: str, variables: dict) -> str:
    template_path = f"bot/modules/mailing/templates/{template_name}.txt"
    if not os.path.exists(template_path):
        return "Шаблон не найден"
    try:
        async with aiofiles.open(template_path, "r", encoding="utf-8") as f:
            content = await f.read()
        # Простая замена {{ name }} → без Jinja2
        text = content
        for key, value in variables.items():
            text = text.replace(f"{{{{ {key} }}}}", str(value))
            text = text.replace(f"{{ {key} }}", str(value))
        return text
    except:
        return "Ошибка чтения шаблона"

# === ОСНОВНАЯ ФУНКЦИЯ РАССЫЛКИ ===
async def run_mailing(mailing_id: int):
    async with async_session() as session:
        mailing = await session.get(Mailing, mailing_id)
        if not mailing or mailing.status != "draft":
            return

        users = (await session.execute(select(User))).scalars().all()
        mailing.status = "running"
        await session.commit()

        sent = delivered = 0
        for user in users:
            try:
                # Формируем текст
                if mailing.template != "manual" and mailing.template:
                    text = await render_template(mailing.template, {"name": user.first_name or "Друг"})
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
                    await bot.send_photo(user.user_id, mailing.photo, caption=text, reply_markup=kb)
                else:
                    await bot.send_message(user.user_id, text, reply_markup=kb, disable_web_page_preview=True)
                
                delivered += 1
            except:
                pass  # заблокировал бота

            sent += 1
            mailing.sent = sent
            mailing.delivered = delivered
            await session.commit()

            # Антибан
            await asyncio.sleep(random.uniform(0.028, 0.045))

        mailing.status = "finished"
        await session.commit()