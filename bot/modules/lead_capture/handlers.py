<<<<<<< HEAD
﻿from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, ReplyKeyboardRemove
=======
﻿# bot/modules/lead_capture/handlers.py — 100% РАБОЧИЙ 2025 (с сохранением в базу)
from aiogram import Router, F
from aiogram.types import Message, ReplyKeyboardRemove
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from bot.modules.lead_capture.forms import LeadForm
from bot.modules.lead_export.google_sheets import append_to_sheet
from bot.modules.lead_export.manager_notify import notify_manager
from database.models import async_session, User
from sqlalchemy import select
from datetime import datetime
import re
>>>>>>> a9e0c52b4eceb78be98320ea53bfef732ec2a7fe

router = Router(name="lead_capture")

<<<<<<< HEAD
# Храним данные пользователей
user_data = {}

# Универсальная функция старта формы
async def start_lead(obj):
    user_id = obj.from_user.id
    user_data[user_id] = {"step": 1}
    
    if isinstance(obj, CallbackQuery):
        await obj.message.delete()  # убираем старое сообщение с кнопками
        msg = await obj.message.answer("Отлично! Как тебя зовут?", reply_markup=ReplyKeyboardRemove())
    else:
        msg = await obj.answer("Отлично! Как тебя зовут?", reply_markup=ReplyKeyboardRemove())
    
    # Сохраняем message_id, чтобы потом можно было редактировать (по желанию)
    user_data[user_id]["msg_id"] = msg.message_id

# Старт по инлайн-кнопке
@router.callback_query(F.data == "start_lead")
async def start_from_button(call: CallbackQuery):
    await start_lead(call)
    await call.answer()

# Основной обработчик всех сообщений во время формы
@router.message()
async def handle_lead_steps(message: Message):
    user_id = message.from_user.id
    if user_id not in user_data:
        return  # не в форме — пропускаем

    step = user_data[user_id]["step"]

    if step == 1:
        user_data[user_id]["name"] = message.text.strip()
        user_data[user_id]["step"] = 2
        await message.answer("Супер! Теперь номер телефона (можно с +7, 8 или просто цифры):")

    elif step == 2:
        user_data[user_id]["phone"] = message.text.strip()
        user_data[user_id]["step"] = 3
        await message.answer("Отлично! И последний шаг — e-mail для связи\n(или напиши «пропустить»):")

    elif step == 3:
        email = message.text.strip()
        if email.lower() in ["пропустить", "skip", "без email", "без почты"]:
            email = "не указан"
        user_data[user_id]["email"] = email

        # Формируем данные
        data = {
            "name": user_data[user_id]["name"],
            "phone": user_data[user_id]["phone"],
            "email": user_data[user_id]["email"],
            "user_id": user_id,
            "username": message.from_user.username or "Нет"
        }

        # Отправляем в таблицу и менеджеру
        try:
            from bot.modules.lead_export.google_sheets import append_to_sheet
            from bot.modules.lead_export.manager_notify import notify_manager
            append_to_sheet(data)
            await notify_manager(data)
        except Exception as e:
            print("Ошибка при экспорте лида:", e)

        # Успешное завершение
        await message.answer("Заявка принята! Менеджер свяжется с тобой в ближайшее время ❤️")

        # Чистим данные
        del user_data[user_id]
=======
@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    await message.answer(
        "Привет! Оставь заявку на доступ\n\nКак тебя зовут?",
        reply_markup=ReplyKeyboardRemove()
    )
    await state.set_state(LeadForm.waiting_name)

@router.message(LeadForm.waiting_name)
async def get_name(message: Message, state: FSMContext):
    name = message.text.strip()
    if not name:
        await message.answer("Имя не может быть пустым! Напиши ещё раз:")
        return
    await state.update_data(name=name)
    await message.answer("Отлично! Теперь номер телефона (например 79123456789):")
    await state.set_state(LeadForm.waiting_phone)

@router.message(LeadForm.waiting_phone)
async def get_phone(message: Message, state: FSMContext):
    phone = re.sub(r"\D", "", message.text)
    if not (len(phone) == 11 and phone.startswith("7")) and not (len(phone) == 10 and phone.startswith("9")):
        await message.answer("Некорректный номер. Введи 11 цифр, начиная с 7")
        return
    if len(phone) == 10:
        phone = "7" + phone
    await state.update_data(phone="+" + phone)
    await message.answer("И последний шаг — твой e-mail:")
    await state.set_state(LeadForm.waiting_email)

@router.message(LeadForm.waiting_email)
async def get_email(message: Message, state: FSMContext):
    email = message.text.strip()
    if "@" not in email or "." not in email.split("@")[-1]:
        await message.answer("Проверь e-mail и напиши ещё раз:")
        return
    
    data = await state.get_data()
    full_data = {
        "name": data["name"],
        "phone": data["phone"],
        "email": email,
        "user_id": message.from_user.id,
        "username": message.from_user.username or "Нет"
    }

    # СОХРАНЯЕМ ПОЛЬЗОВАТЕЛЯ В БАЗУ — РАБОЧИЙ КОД ДЛЯ SQLALCHEMY 2.0+
    async with async_session() as session:
        result = await session.execute(select(User).where(User.user_id == message.from_user.id))
        user = result.scalar_one_or_none()
        if not user:
            new_user = User(
                user_id=message.from_user.id,
                username=message.from_user.username,
                first_name=message.from_user.first_name or data["name"],
                joined_at=datetime.utcnow()
            )
            session.add(new_user)
            await session.commit()

    # Отправка в Google-таблицу и менеджеру
    success = append_to_sheet(full_data)
    if success:
        await notify_manager(full_data)
        await message.answer("Готово! Заявка принята\nМенеджер свяжется в ближайшее время!")
    else:
        await message.answer("Техническая ошибка, попробуй позже.")
    
    await state.clear()
>>>>>>> a9e0c52b4eceb78be98320ea53bfef732ec2a7fe
