from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from .faq_data import FAQ_DB

router = Router(name="faq")

def get_faq_list_kb():
    kb = [[InlineKeyboardButton(text=item["question"], callback_data=f"faq_{i}")] for i, item in enumerate(FAQ_DB)]
    kb.append([InlineKeyboardButton(text="Назад", callback_data="back_to_start")])
    return InlineKeyboardMarkup(inline_keyboard=kb)

def get_back_kb():
    return InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="Назад в FAQ", callback_data="show_faq_list")]])

@router.callback_query(F.data == "show_faq")
async def show_faq_list(call: CallbackQuery):
    await call.message.edit_text(
        "Часто задаваемые вопросы:",
        reply_markup=get_faq_list_kb()
    )
    await call.answer()

@router.callback_query(F.data.startswith("faq_"))
async def show_faq_answer(call: CallbackQuery):
    idx = int(call.data.split("_")[1])
    item = FAQ_DB[idx]
    await call.message.edit_text(
        item["answer"] + "\n\nНажми «Назад», чтобы вернуться",
        reply_markup=get_back_kb(),
        disable_web_page_preview=True
    )
    await call.answer()

@router.callback_query(F.data == "show_faq_list")
async def back_to_faq(call: CallbackQuery):
    await call.message.edit_text("Часто задаваемые вопросы:", reply_markup=get_faq_list_kb())
    await call.answer()

@router.callback_query(F.data == "back_to_start")
async def back_to_main(call: CallbackQuery):
    from bot.modules.main_menu.handlers import get_start_kb
    await call.message.edit_text(
        "Привет! Я бот-подписка для экспертов\n\nЧто тебя интересует?",
        reply_markup=get_start_kb()
    )
    await call.answer()
