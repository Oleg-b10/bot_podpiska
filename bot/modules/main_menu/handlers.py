from aiogram import Router, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from config.settings import SUPPORT_CHAT_ID
from bot.core.loader import bot
import logging

log = logging.getLogger(__name__)

router = Router(name="main_menu")

# ДВА СЛОВАРЯ:
active_support = {}   # user_id → thread_id (активные чаты)
all_user_topics = {}  # user_id → thread_id (все когда-либо созданные топики — НАВСЕГДА)

def get_start_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="FAQ", callback_data="show_faq")],
        [InlineKeyboardButton(text="Оставить заявку", callback_data="start_lead")],
        [InlineKeyboardButton(text="Поддержка", callback_data="open_support")],
    ])

@router.message(Command("start"))
async def cmd_start(message: Message):
    await message.answer("Привет! Я бот-подписка для экспертов\n\nЧто тебя интересует?", reply_markup=get_start_kb())

@router.callback_query(F.data == "open_support")
async def open_support(call):
    user_id = call.from_user.id

    # ЕСЛИ УЖЕ ЕСТЬ АКТИВНЫЙ ЧАТ — НЕ ДАЁМ ОТКРЫТЬ ЕЩЁ
    if user_id in active_support:
        await call.answer("Чат с поддержкой уже открыт!", show_alert=True)
        return

    # ЕСЛИ У ПОЛЬЗОВАТЕЛЯ УЖЕ БЫЛ ТОПИК — ВОЗВРАЩАЕМ ЕГО В НЕГО
    if user_id in all_user_topics:
        thread_id = all_user_topics[user_id]
        active_support[user_id] = thread_id
        log.info(f"[ПОДДЕРЖКА] Восстановлен старый топик {thread_id} для {user_id}")
        
        await call.message.edit_text(
            "Вы вернулись в чат с поддержкой!\nПишите — менеджер ответит.",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="Закрыть чат", callback_data="close_support")]
            ])
        )
        await call.answer()
        return

    # ЕСЛИ ВПЕРВЫЕ — СОЗДАЁМ НОВЫЙ (только при первом сообщении, ниже)
    active_support[user_id] = None
    log.info(f"[ПОДДЕРЖКА] ОТКРЫТА НОВАЯ для {user_id}")

    await call.message.edit_text(
        "Напишите ваш вопрос — ответим максимально быстро!",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Закрыть чат", callback_data="close_support")]
        ])
    )
    await call.answer()

@router.callback_query(F.data == "close_support")
async def close_support(call):
    user_id = call.from_user.id
    active_support.pop(user_id, None)
    log.info(f"[ПОДДЕРЖКА] ЗАКРЫТА для {user_id}")
    await call.message.edit_text("Чат закрыт", reply_markup=get_start_kb())
    await call.answer()

# КЛИЕНТ → ТОПИК
@router.message(F.chat.type == "private")
async def client_to_support(message: Message):
    user_id = message.from_user.id
    if user_id not in active_support:
        return

    thread_id = active_support[user_id]

    try:
        # СОЗДАЁМ ТОПИК ТОЛЬКО ОДИН РАЗ — ЕСЛИ ЕЩЁ НЕТ
        if thread_id is None:
            topic = await bot.create_forum_topic(
                chat_id=SUPPORT_CHAT_ID,
                name=f"{message.from_user.full_name}"
            )
            thread_id = topic.message_thread_id
            active_support[user_id] = thread_id
            all_user_topics[user_id] = thread_id  # ← ЗАПОМИНАЕМ НАВСЕГДА
            log.info(f"[ПОДДЕРЖКА] ТОПИК СОЗДАН НАВСЕГДА: {thread_id} для {user_id}")

            await bot.send_message(
                SUPPORT_CHAT_ID,
                f"Новый клиент!\nИмя: {message.from_user.full_name}\nID: <code>{user_id}</code>",
                parse_mode="HTML",
                message_thread_id=thread_id
            )

        # Пересылаем
        forwarded = await message.forward(SUPPORT_CHAT_ID, message_thread_id=thread_id)
        if not hasattr(bot, "message_to_user"):
            bot.message_to_user = {}
        bot.message_to_user[forwarded.message_id] = user_id

        await message.answer("Сообщение отправлено менеджеру")

    except Exception as e:
        log.error(f"Ошибка: {e}")
        await message.answer("Ошибка")

# ГРУППА → КЛИЕНТ
@router.message(F.chat.id == SUPPORT_CHAT_ID, F.reply_to_message, F.reply_to_message.forward_from)
async def support_to_client(message: Message):
    replied_id = message.reply_to_message.message_id
    if not hasattr(bot, "message_to_user") or replied_id not in bot.message_to_user:
        return

    user_id = bot.message_to_user[replied_id]
    try:
        await message.copy_to(chat_id=user_id)
        log.info(f"Ответ доставлен клиенту {user_id}")
    except Exception as e:
        log.error(f"Не удалось отправить: {e}")

@router.callback_query(F.data == "back_to_start")
async def back_to_start(call):
    await call.message.edit_text("Привет! Я бот-подписка для экспертов\n\nЧто тебя интересует?", reply_markup=get_start_kb())
    await call.answer()
