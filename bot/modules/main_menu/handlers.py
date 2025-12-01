from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from bot.core.states import BotStates
from aiogram.fsm.context import FSMContext

router = Router(name="main_menu")

def get_start_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="FAQ", callback_data="show_faq")],
        [InlineKeyboardButton(text="Оставить заявку", callback_data="start_lead")],
        [InlineKeyboardButton(text="Поддержка", callback_data="open_support")],
    ])

@router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Привет! Я бот-подписка для экспертов\n\nЧто тебя интересует?", reply_markup=get_start_kb())

@router.callback_query(F.data == "start_lead")
async def start_lead(call: CallbackQuery, state: FSMContext):
    await state.set_state(BotStates.lead_name)
    await call.message.delete()
    await call.message.answer("Отлично! Как тебя зовут?")
    await call.answer()

@router.callback_query(F.data == "open_support")
async def open_support(call: CallbackQuery, state: FSMContext):
    await state.set_state(BotStates.in_support)
    await call.message.edit_text(
        "Чат с поддержкой открыт!\nПишите сообщение:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Закрыть чат", callback_data="close_support")]  # ← ИСПРАВЛЕНО: двойной список!
        ])
    )
    await call.answer()

@router.callback_query(F.data == "close_support")
async def close_support(call: CallbackQuery, state: FSMContext):
    await state.clear()
    await call.message.edit_text("Чат закрыт", reply_markup=get_start_kb())
    await call.answer()
