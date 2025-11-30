from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from .faq_data import FAQ_DB
from bot.modules.main_menu.handlers import get_main_menu

def get_faq_menu():
    kb = [[KeyboardButton(text=item["question"])] for item in FAQ_DB]
    kb.append([KeyboardButton(text="Назад в главное меню")])
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

def get_back_kb():
    return ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="Назад в FAQ")]], resize_keyboard=True)

def get_faq_inline():
    ikb = [[InlineKeyboardButton(text=item["question"], callback_data=f"faq_{i}")] for i, item in enumerate(FAQ_DB)]
    return InlineKeyboardMarkup(inline_keyboard=ikb)
