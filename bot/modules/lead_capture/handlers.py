from aiogram import Router, F
from aiogram.types import Message, ReplyKeyboardRemove
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from bot.modules.lead_capture.forms import LeadForm
from bot.modules.lead_export.google_sheets import append_to_sheet
from bot.modules.lead_export.manager_notify import notify_manager
import re, asyncio

router = Router()

@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    await message.answer("Привет! Оставь заявку на доступ 👇\n\nКак тебя зовут?", reply_markup=ReplyKeyboardRemove())
    await state.set_state(LeadForm.waiting_name)

@router.message(LeadForm.waiting_name)
async def get_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text.strip())
    await message.answer("Отлично! Теперь номер телефона (например 79123456789):")
    await state.set_state(LeadForm.waiting_phone)

@router.message(LeadForm.waiting_phone)
async def get_phone(message: Message, state: FSMContext):
    phone = re.sub(r"\D", "", message.text)
    if not (len(phone) == 11 and phone.startswith("7")) and not (len(phone) == 10 and phone.startswith("9")):
        await message.answer("Некорректный номер. Введи 11 цифр, начиная с 7")
        return
    if len(phone) == 10: phone = "7" + phone
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
    success = append_to_sheet(full_data)
    if success:
        await notify_manager(full_data)
        await message.answer("Готово! Заявка принята ❤️\nМенеджер свяжется в ближайшее время!")
    else:
        await message.answer("Техническая ошибка, попробуй позже.")
    await state.clear()
