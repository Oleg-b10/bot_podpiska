from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from bot.core.states import BotStates
from bot.modules.lead_export.google_sheets import append_to_sheet
from bot.modules.lead_export.manager_notify import notify_manager

router = Router(name="lead_capture")

@router.message(BotStates.lead_name)
async def get_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text.strip())
    await state.set_state(BotStates.lead_phone)
    await message.answer("Теперь номер телефона (например +79123456789):")

@router.message(BotStates.lead_phone)
async def get_phone(message: Message, state: FSMContext):
    phone = "".join(c for c in message.text if c.isdigit())
    if len(phone) not in [10, 11]:
        await message.answer("Неправильный номер. Пример: +79123456789")
        return
    if len(phone) == 10:
        phone = "7" + phone
    await state.update_data(phone="+" + phone)
    await state.set_state(BotStates.lead_email)
    await message.answer("И email (или напиши «пропустить»):")

@router.message(BotStates.lead_email)
async def get_email(message: Message, state: FSMContext):
    email = message.text.strip()
    if email.lower() in ["пропустить", "skip", "нет"]:
        email = "не указан"
    
    data = await state.get_data()
    full_data = {
        "name": data["name"],
        "phone": data["phone"],
        "email": email,
        "user_id": message.from_user.id,
        "username": message.from_user.username or "Нет"
    }
    
    try:
        append_to_sheet(full_data)
        await notify_manager(full_data)
        await message.answer("Готово! Заявка принята ❤️")
    except Exception as e:
        await message.answer("Ошибка отправки, попробуй позже")
    
    await state.clear()
