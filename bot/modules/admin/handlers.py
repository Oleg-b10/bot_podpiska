# bot/modules/admin/handlers.py — ФИНАЛЬНЫЙ КОД 2025 (ВСЁ РАБОТАЕТ)
from aiogram import Router, F
from aiogram.types import (
    Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, BufferedInputFile
)
from aiogram.filters import Command
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from config.features import ADMIN_IDS
from database.models import async_session, User, Mailing
from bot.modules.mailing.scheduler import schedule_mailing
from bot.modules.mailing.sender import render_template
from bot.core.loader import bot
from datetime import datetime, timedelta
from sqlalchemy import select, func, or_
import matplotlib.pyplot as plt
import io
import os
import aiofiles

router = Router()

class CreateMailing(StatesGroup):
    text = State()
    photo = State()
    button_text = State()
    button_url = State()
    confirm = State()
    save_template_name = State()  # ← ЭТОЙ СТРОКИ НЕ БЫЛО — ИЗ-ЗА ЭТОГО ПАДАЛО!

# === АДМИН-ПАНЕЛЬ ===
@router.message(Command("admin"), F.from_user.id.in_(ADMIN_IDS))
async def admin_menu(message: Message):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Статистика", callback_data="stats")],
        [InlineKeyboardButton(text="Создать рассылку", callback_data="new_mailing")],
    ])
    await message.answer("Админ-панель v2025", reply_markup=kb)

# === СТАТИСТИКА ===
@router.callback_query(F.data == "stats")
async def show_stats(call: CallbackQuery):
    async with async_session() as session:
        total_users = (await session.execute(select(func.count(User.id)))).scalar_one()

        today = datetime.utcnow().date()
        week_ago = today - timedelta(days=7)
        month_ago = today - timedelta(days=30)

        users_today = (await session.execute(select(func.count(User.id)).where(func.date(User.joined_at) == today))).scalar_one()
        users_week = (await session.execute(select(func.count(User.id)).where(User.joined_at >= week_ago))).scalar_one()
        users_month = (await session.execute(select(func.count(User.id)).where(User.joined_at >= month_ago))).scalar_one()

        text = f"""СТАТИСТИКА БОТА

Всего пользователей: <b>{total_users}</b>
• За сегодня: <b>+{users_today}</b>
• За неделю: <b>+{users_week}</b>
• За месяц: <b>+{users_month}</b>"""

        fig, ax = plt.subplots(figsize=(9, 5))
        periods = ["Сегодня", "Неделя", "Месяц"]
        values = [users_today, users_week, users_month]
        colors = ["#00ff88", "#0088ff", "#ff8800"]
        bars = ax.bar(periods, values, color=colors)
        ax.set_title("Новые пользователи", fontsize=16, pad=20)
        ax.set_ylabel("Количество")
        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height + max(values)*0.01,
                    f'{int(height)}', ha='center', va='bottom', fontsize=12)

        buffer = io.BytesIO()
        plt.savefig(buffer, format='png', bbox_inches='tight', dpi=100)
        buffer.seek(0)
        plt.close(fig)

        photo = BufferedInputFile(buffer.read(), filename="stats.png")

        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Назад", callback_data="back_to_admin")]
        ])

        await call.message.answer_photo(photo, caption=text, parse_mode="HTML", reply_markup=kb)
    await call.answer()

@router.callback_query(F.data == "back_to_admin")
async def back_to_admin(call: CallbackQuery):
    await admin_menu(call.message)
    await call.answer()

# === СОЗДАНИЕ РАССЫЛКИ С СЕГМЕНТАМИ ===
@router.callback_query(F.data == "new_mailing")
async def choose_segments(call: CallbackQuery, state: FSMContext):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="☐ Все пользователи", callback_data="seg_all")],
        [InlineKeyboardButton(text="☐ Только лиды", callback_data="seg_leads")],
        [InlineKeyboardButton(text="☐ Только оплатившие", callback_data="seg_paid")],
        [InlineKeyboardButton(text="☐ Активные 7 дней", callback_data="seg_active7")],
        [InlineKeyboardButton(text="☐ Активные 30 дней", callback_data="seg_active30")],
        [InlineKeyboardButton(text="☐ Неактивные", callback_data="seg_inactive")],
        [InlineKeyboardButton(text="Далее →", callback_data="segments_done")],
    ])
    await call.message.edit_text("Выбери сегменты (можно несколько):", reply_markup=kb)
    await state.update_data(selected_segments=[])
    await call.answer()

@router.callback_query(F.data.startswith("seg_"))
async def toggle_segment(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    segments = data.get("selected_segments", [])
    seg = call.data.split("_")[1]

    if seg in segments:
        segments.remove(seg)
    else:
        segments.append(seg)

    await state.update_data(selected_segments=segments)

    kb_buttons = []
    for s, name in [
        ("all", "Все пользователи"),
        ("leads", "Только лиды"),
        ("paid", "Только оплатившие"),
        ("active7", "Активные 7 дней"),
        ("active30", "Активные 30 дней"),
        ("inactive", "Неактивные"),
    ]:
        check = "☑" if s in segments else "☐"
        kb_buttons.append([InlineKeyboardButton(text=f"{check} {name}", callback_data=f"seg_{s}")])
    kb_buttons.append([InlineKeyboardButton(text="Далее →", callback_data="segments_done")])

    kb = InlineKeyboardMarkup(inline_keyboard=kb_buttons)
    await call.message.edit_reply_markup(reply_markup=kb)
    await call.answer()

@router.callback_query(F.data == "segments_done")
async def segments_done(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    if not data.get("selected_segments"):
        await call.answer("Выбери хотя бы один сегмент!", show_alert=True)
        return

    await call.message.edit_text("Напиши текст рассылки:")
    await state.set_state(CreateMailing.text)
    await call.answer()

# === ОБЩИЙ FSM РАССЫЛКИ ===
@router.message(CreateMailing.text)
async def get_text(message: Message, state: FSMContext):
    await state.update_data(text=message.text)
    await ask_photo(message, state)

async def ask_photo(message: Message, state: FSMContext):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Без фото", callback_data="no_photo")],
    ])
    await message.answer("Пришли фото или нажми ниже:", reply_markup=kb)
    await state.set_state(CreateMailing.photo)

@router.callback_query(F.data == "no_photo")
async def no_photo(call: CallbackQuery, state: FSMContext):
    await state.update_data(photo=None)
    await ask_button(call.message, state)
    await call.answer()

@router.message(CreateMailing.photo)
async def get_photo(message: Message, state: FSMContext):
    if not message.photo:
        await message.answer("Пришли фото или «Без фото»")
        return
    await state.update_data(photo=message.photo[-1].file_id)
    await ask_button(message, state)

async def ask_button(message: Message, state: FSMContext):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Без кнопки", callback_data="no_button")],
    ])
    await message.answer("Текст кнопки (или «Без кнопки»):", reply_markup=kb)
    await state.set_state(CreateMailing.button_text)

@router.callback_query(F.data == "no_button")
async def no_button(call: CallbackQuery, state: FSMContext):
    await state.update_data(button_text=None, button_url=None)
    await show_final_preview(call.message, state)
    await call.answer()

@router.message(CreateMailing.button_text)
async def get_button_text(message: Message, state: FSMContext):
    text = message.text.strip()
    if text.lower() in ["без кнопки", "нет"]:
        await state.update_data(button_text=None, button_url=None)
    else:
        await state.update_data(button_text=text)
        await message.answer("Ссылка для кнопки:")
        await state.set_state(CreateMailing.button_url)
        return
    await show_final_preview(message, state)

@router.message(CreateMailing.button_url)
async def get_button_url(message: Message, state: FSMContext):
    url = message.text.strip()
    if url.startswith("@"):
        url = "https://t.me/" + url[1:]
    await state.update_data(button_url=url)
    await show_final_preview(message, state)

# === ФИНАЛЬНОЕ ПРЕВЬЮ ===
async def show_final_preview(message: Message, state: FSMContext):
    data = await state.get_data()
    preview_text = data.get("text", "")

    kb = None
    if data.get("button_text"):
        url = data.get("button_url", "")
        if url.startswith("@"):
            url = "https://t.me/" + url[1:]
        kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text=data["button_text"], url=url)]])

    await message.answer("<b>Финальное превью</b>\n\nТак увидит получатель:", parse_mode="HTML")
    
    if data.get("photo"):
        await message.answer_photo(data["photo"], caption=preview_text, reply_markup=kb)
    else:
        await message.answer(preview_text, reply_markup=kb, disable_web_page_preview=True)

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Запустить сейчас", callback_data="run_now")],
        [InlineKeyboardButton(text="Сохранить как шаблон", callback_data="save_as_template")],
        [InlineKeyboardButton(text="Отменить", callback_data="cancel_mailing")],
    ])
    await message.answer("Готово! Что дальше?", reply_markup=kb)
    await state.set_state(CreateMailing.confirm)

# === ЗАПУСК РАССЫЛКИ ===
@router.callback_query(F.data == "run_now")
async def run_now(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    
    async with async_session() as session:
        mailing = Mailing(
            name=data.get("name", "Без имени"),
            template=data.get("template_name", "manual"),
            text=data.get("text"),
            photo=data.get("photo"),
            button_text=data.get("button_text"),
            button_url=data.get("button_url"),
            segments=data.get("selected_segments", ["all"])
        )
        session.add(mailing)
        await session.commit()
        await session.refresh(mailing)
    
    schedule_mailing(mailing.id)
    await call.message.edit_text("Рассылка запущена по выбранным сегментам!")
    await state.clear()

# === СОХРАНЕНИЕ КАК ШАБЛОН ===
@router.callback_query(F.data == "save_as_template")
async def save_as_template(call: CallbackQuery, state: FSMContext):
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="Назад", callback_data="back_to_preview")]])
    await call.message.edit_text("Имя нового шаблона:", reply_markup=kb)
    await state.set_state(CreateMailing.save_template_name)
    await call.answer()

@router.message(CreateMailing.save_template_name)
async def do_save(message: Message, state: FSMContext):
    name = message.text.strip().lower().replace(" ", "_")
    if not name or "/" in name:
        await message.answer("Некорректное имя!")
        return
    data = await state.get_data()
    text = data.get("text", "")
    if data.get("source") == "template":
        text = await render_template(data["template_name"], {"name": "{{ name }}"})

    async with aiofiles.open(f"bot/modules/mailing/templates/{name}.txt", "w", encoding="utf-8") as f:
        await f.write(text)
    if data.get("photo"):
        file = await bot.get_file(data["photo"])
        await bot.download_file(file.file_path, f"bot/modules/mailing/templates/{name}.jpg")
    
    await message.answer(f"Шаблон «{name}» сохранён!")
    await state.clear()

# === ОТМЕНА ===
@router.callback_query(F.data == "cancel_mailing")
async def cancel(call: CallbackQuery, state: FSMContext):
    await call.message.edit_text("Отменено")
    await state.clear()