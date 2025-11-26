from aiogram import Router, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardRemove

router = Router(name="main_menu")

# Главное меню — 2 инлайн-кнопки
def get_start_kb():
    kb = [
        [InlineKeyboardButton(text="FAQ", callback_data="show_faq")],
        [InlineKeyboardButton(text="Оставить заявку", callback_data="start_lead")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=kb)

@router.message(F.text == "/start")
async def cmd_start(message: Message):
    await message.answer(
        "Привет! Я бот-подписка для экспертов\n\nЧто тебя интересует?",
        reply_markup=get_start_kb()
    )
