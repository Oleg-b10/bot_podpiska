from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from config.features import ADMIN_IDS
from database.models import async_session, User
from datetime import datetime, timedelta
from sqlalchemy import select, func, or_

router = Router()

# Состояния
class SegmentState:
    choosing = "choosing_segments"

# === ВЫБОР СЕГМЕНТОВ ===
@router.callback_query(F.data == "choose_segments")
async def choose_segments(call: CallbackQuery, state: FSMContext):
    kb_buttons = []
    segments_info = [
        ("all", "Все пользователи"),
        ("leads", "Только лиды"),
        ("paid", "Только оплатившие"),
        ("active7", "Активные 7 дней"),
        ("active30", "Активные 30 дней"),
        ("inactive", "Неактивные"),
    ]
    
    current = (await state.get_data()).get("segments", [])
    
    for code, name in segments_info:
        check = "☑" if code in current else "☐"
        kb_buttons.append([InlineKeyboardButton(text=f"{check} {name}", callback_data=f"toggle_seg:{code}")])
    
    kb_buttons.append([InlineKeyboardButton(text="Готово →", callback_data="segments_done")])
    
    kb = InlineKeyboardMarkup(inline_keyboard=kb_buttons)
    await call.message.edit_text("Выбери сегменты для рассылки:", reply_markup=kb)
    await call.answer()

# Переключение
@router.callback_query(F.data.startswith("toggle_seg:"))
async def toggle_segment(call: CallbackQuery, state: FSMContext):
    code = call.data.split(":")[1]
    data = await state.get_data()
    segments = data.get("segments", [])
    
    if code in segments:
        segments.remove(code)
    else:
        segments.append(code)
    
    await state.update_data(segments=segments)
    await choose_segments(call, state)

# Готово — возвращаем выбранные сегменты
@router.callback_query(F.data == "segments_done")
async def segments_done(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    segments = data.get("segments", ["all"])
    await state.update_data(segments=segments)
    
    await call.message.edit_text(f"Выбрано сегментов: {len(segments)}\nТеперь напиши текст рассылки:")
    await state.set_state("mailing_text")  # дальше админка продолжает
    await call.answer()
