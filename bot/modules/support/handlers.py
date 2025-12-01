from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from bot.core.states import BotStates
from config.settings import SUPPORT_CHAT_ID
from bot.core.loader import bot

router = Router(name="support")

active_support = {}   # user_id → thread_id
all_user_topics = {}  # user_id → thread_id навсегда

@router.message(BotStates.in_support)
async def handle_support(message: Message, state: FSMContext):
    user_id = message.from_user.id
    thread_id = active_support.get(user_id)

    try:
        if thread_id is None:
            topic = await bot.create_forum_topic(
                chat_id=SUPPORT_CHAT_ID,
                name=message.from_user.full_name or "Клиент"
            )
            thread_id = topic.message_thread_id
            active_support[user_id] = thread_id
            all_user_topics[user_id] = thread_id

            await bot.send_message(
                SUPPORT_CHAT_ID,
                f"Новый клиент!\n{message.from_user.full_name}\nID: <code>{user_id}</code>",
                parse_mode="HTML",
                message_thread_id=thread_id
            )

        fwd = await message.forward(SUPPORT_CHAT_ID, message_thread_id=thread_id)
        if not hasattr(bot, "msg_map"):
            bot.msg_map = {}
        bot.msg_map[fwd.message_id] = user_id

        await message.answer("Сообщение отправлено менеджеру ✓")
    except Exception as e:
        await message.answer("Ошибка отправки")

# Ответы из группы
@router.message(F.chat.id == SUPPORT_CHAT_ID, F.reply_to_message, F.reply_to_message.forward_from)
async def reply_from_support(message: Message):
    if hasattr(bot, "msg_map") and message.reply_to_message.message_id in bot.msg_map:
        await message.copy_to(bot.msg_map[message.reply_to_message.message_id])
