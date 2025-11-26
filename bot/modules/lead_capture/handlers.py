from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, ReplyKeyboardRemove

router = Router(name="lead_capture")

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
