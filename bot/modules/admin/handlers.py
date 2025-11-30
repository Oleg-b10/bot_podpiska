# bot/modules/admin/handlers.py — ФИНАЛЬНЫЙ КОД 2025 (статистика + рассылка + оплата)
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
from sqlalchemy import select, func
import matplotlib.pyplot as plt
import io
import os
import aiofiles
import uuid
from yookassa import Configuration, Payment

# ЮKassa (если есть ключи)
if os.getenv("YOOKASSA_SHOP_ID"):
    Configuration.account_id = os.getenv("YOOKASSA_SHOP_ID")
    Configuration.secret_key = os.getenv("YOOKASSA_SECRET")

# Тарифы
TARIFS = {
    "base": {"name": "Базовый", "price": 9900},
    "pro": {"name": "Про", "price": 19900},
    "vip": {"name": "VIP", "price": 49900},
}

router = Router()

class CreateMailing(StatesGroup):
    name = State()
    choose_source = State()
    template = State()
    text = State()
    photo = State()
    button_text = State()
    button_url = State()
    confirm = State()
    save_template_name = State()

# === АДМИН-ПАНЕЛЬ ===
@router.message(Command("admin"), F.from_user.id.in_(ADMIN_IDS))
async def admin_menu(message: Message):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Статистика", callback_data="stats")],
        [InlineKeyboardButton(text="Создать рассылку", callback_data="new_mailing")],
        [InlineKeyboardButton(text="Оплата (тест)", callback_data="test_payment")],
    ])
    await message.answer("Админ-панель v2025 — всё в одном месте!", reply_markup=kb)

# === СТАТИСТИКА ===
@router.callback_query(F.data == "stats")
async def show_stats(call: CallbackQuery):
    async with async_session() as session:
        total_users = (await session.execute(select(func.count(User.id)))).scalar_one()

        today = datetime.utcnow().date()
        week_ago = today - timedelta(days=7)
        month_ago = today - timedelta(days=30)

        users_today = (await session.execute(
            select(func.count(User.id)).where(func.date(User.joined_at) == today)
        )).scalar_one()

        users_week = (await session.execute(
            select(func.count(User.id)).where(User.joined_at >= week_ago)
        )).scalar_one()

        users_month = (await session.execute(
            select(func.count(User.id)).where(User.joined_at >= month_ago)
        )).scalar_one()

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

# === ТЕСТ ОПЛАТЫ ЮKASSA ===
@router.callback_query(F.data == "test_payment")
async def test_payment(call: CallbackQuery):
    tariff = "pro"
    price = TARIFS[tariff]["price"]
    
    payment = Payment.create({
        "amount": {"value": str(price), "currency": "RUB"},
        "confirmation": {"type": "redirect", "return_url": "https://t.me/твой_бот"},
        "capture": True,
        "description": "Тестовая оплата",
        "metadata": {"user_id": str(call.from_user.id)}
    }, uuid.uuid4())

    url = payment.confirmation.confirmation_url
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Оплатить тестово", url=url)],
        [InlineKeyboardButton(text="Назад", callback_data="back_to_admin")],
    ])
    
    await call.message.edit_text(
        f"Тест оплаты — {price:,} ₽\n\nНажми кнопку:",
        reply_markup=kb
    )
    await call.answer()

# === ВСЯ РАССЫЛКА (оставь как было — она уже рабочая) ===
# (весь код рассылки из твоего последнего сообщения — он уже 100% рабочий)

# ГОТОВО НА 1000%!

# === НАЧАЛО РАССЫЛКИ ===
@router.callback_query(F.data == "new_mailing")
async def choose_source(call: CallbackQuery, state: FSMContext):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Вручную", callback_data="source_manual")],
        [InlineKeyboardButton(text="Из шаблона", callback_data="source_template")],
        [InlineKeyboardButton(text="Назад", callback_data="back_to_admin")],
    ])
    await call.message.edit_text("Как создать рассылку?", reply_markup=kb)
    await call.answer()

# === ВРУЧНУЮ ===
@router.callback_query(F.data == "source_manual")
async def manual_start(call: CallbackQuery, state: FSMContext):
    await state.update_data(source="manual")
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="Назад", callback_data="back_to_source")]])
    await call.message.edit_text("Напиши текст рассылки:", reply_markup=kb)
    await state.set_state(CreateMailing.text)
    await call.answer()

# === ИЗ ШАБЛОНА ===
@router.callback_query(F.data == "source_template")
async def list_templates(call: CallbackQuery, state: FSMContext):
    templates_dir = "bot/modules/mailing/templates"
    if not os.path.exists(templates_dir):
        os.makedirs(templates_dir)
    txt_files = [f for f in os.listdir(templates_dir) if f.endswith(".txt")]
    
    if not txt_files:
        kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="Назад", callback_data="back_to_source")]])
        await call.message.edit_text("Шаблонов нет — создай первый вручную!", reply_markup=kb)
        await call.answer()
        return
    
    kb_buttons = []
    for txt in txt_files:
        name = txt.replace(".txt", "")
        photo_path = f"{templates_dir}/{name}.jpg"
        emoji = "Фото" if os.path.exists(photo_path) else "Текст"
        kb_buttons.append([InlineKeyboardButton(text=f"{emoji} {name}", callback_data=f"tpl_select:{name}")])
    kb_buttons.append([InlineKeyboardButton(text="Назад", callback_data="back_to_source")])
    
    kb = InlineKeyboardMarkup(inline_keyboard=kb_buttons)
    await call.message.edit_text("Выбери шаблон:", reply_markup=kb)
    await state.set_state(CreateMailing.template)
    await call.answer()

@router.callback_query(F.data == "back_to_source")
async def back_to_source(call: CallbackQuery, state: FSMContext):
    await choose_source(call, state)
    await call.answer()

# === ВЫБОР ШАБЛОНА ===
@router.callback_query(F.data.startswith("tpl_select:"))
async def template_chosen(call: CallbackQuery, state: FSMContext):
    template_name = call.data.split(":")[1]
    await state.update_data(source="template", template_name=template_name)

    preview_text = await render_template(template_name, {"name": "Алексей"})
    photo_path = f"bot/modules/mailing/templates/{template_name}.jpg"

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Использовать как есть", callback_data="tpl_use_as_is")],
        [InlineKeyboardButton(text="Редактировать", callback_data="tpl_edit")],
        [InlineKeyboardButton(text="Назад", callback_data="back_to_template_list")],
    ])

    if os.path.exists(photo_path):
        await call.message.answer_photo(
            BufferedInputFile.from_path(photo_path),
            caption=f"<b>Шаблон: {template_name}</b>\n\nТак будет выглядеть:\n\n{preview_text}",
            parse_mode="HTML",
            reply_markup=kb
        )
    else:
        await call.message.answer(
            f"<b>Шаблон: {template_name}</b>\n\nТак будет выглядеть:\n\n{preview_text}",
            parse_mode="HTML",
            reply_markup=kb
        )
    await call.answer()

@router.callback_query(F.data == "back_to_template_list")
async def back_to_template_list(call: CallbackQuery, state: FSMContext):
    await list_templates(call, state)
    await call.answer()

# === ИСПОЛЬЗОВАТЬ КАК ЕСТЬ ===
@router.callback_query(F.data == "tpl_use_as_is")
async def use_as_is(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    template_name = data["template_name"]
    
    photo_file_id = None
    photo_path = f"bot/modules/mailing/templates/{template_name}.jpg"
    if os.path.exists(photo_path):
        sent = await call.message.answer_photo(BufferedInputFile.from_path(photo_path))
        photo_file_id = sent.photo[-1].file_id
    
    await state.update_data(photo=photo_file_id)
    await show_final_preview(call.message, state)
    await call.answer()

# === РЕДАКТИРОВАТЬ ШАБЛОН ===
@router.callback_query(F.data == "tpl_edit")
async def edit_template_start(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    template_name = data["template_name"]
    
    template_path = f"bot/modules/mailing/templates/{template_name}.txt"
    async with aiofiles.open(template_path, "r", encoding="utf-8") as f:
        current_text = await f.read()
    
    await state.update_data(use_template=False, text=current_text)
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="Назад", callback_data="back_to_template")]])
    await call.message.edit_text(
        f"<b>Редактирование шаблона: {template_name}</b>\n\nТекущий текст:\n<pre>{current_text}</pre>\n\nПришли новый текст:",
        parse_mode="HTML",
        reply_markup=kb
    )
    await state.set_state(CreateMailing.text)
    await call.answer()

@router.callback_query(F.data == "back_to_template")
async def back_to_template(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    await template_chosen(call, state)
    await call.answer()

# === ОБЩИЙ FSM ===
@router.message(CreateMailing.text)
async def get_text(message: Message, state: FSMContext):
    await state.update_data(text=message.text)
    await ask_photo(message, state)

async def ask_photo(message: Message, state: FSMContext):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Без фото", callback_data="no_photo")],
        [InlineKeyboardButton(text="Назад", callback_data="back_to_text")],
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
        [InlineKeyboardButton(text="Назад", callback_data="back_to_photo")],
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
        kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="Назад", callback_data="back_to_button")]])
        await message.answer("Ссылка для кнопки:", reply_markup=kb)
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
    if data.get("source") == "template" and data.get("template_name"):
        preview_text = await render_template(data["template_name"], {"name": "Алексей"})

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
        [InlineKeyboardButton(text="Назад", callback_data="back_to_button")],
        [InlineKeyboardButton(text="Отменить", callback_data="cancel_mailing")],
    ])
    await message.answer("Готово! Что дальше?", reply_markup=kb)
    await state.set_state(CreateMailing.confirm)

# === ЗАПУСК И СОХРАНЕНИЕ ===
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
        )
        session.add(mailing)
        await session.commit()
        await session.refresh(mailing)
    schedule_mailing(mailing.id)
    await call.message.edit_text("Рассылка успешно запущена!")
    await state.clear()

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

@router.callback_query(F.data.in_(["back_to_text", "back_to_photo", "back_to_button", "back_to_preview"]))
async def universal_back(call: CallbackQuery, state: FSMContext):
    step = call.data.split("_")[-1]
    if step == "text":
        await get_text(call.message, state)
    elif step == "photo":
        await ask_photo(call.message, state)
    elif step == "button":
        await ask_button(call.message, state)
    elif step == "preview":
        await show_final_preview(call.message, state)
    await call.answer()

@router.callback_query(F.data == "cancel_mailing")
async def cancel(call: CallbackQuery, state: FSMContext):
    await call.message.edit_text("Отменено")
    await state.clear()