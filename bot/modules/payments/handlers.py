from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
import uuid
import os
from yookassa import Configuration, Payment

router = Router()

# Настройка из .env
Configuration.account_id = os.getenv("YOOKASSA_SHOP_ID")
Configuration.secret_key = os.getenv("YOOKASSA_SECRET")

# Тарифы  меняй как хочешь
TARIFS = {
    "base": {"name": "Базовый", "price": 9900},
    "pro": {"name": "Про", "price": 19900},
    "vip": {"name": "VIP", "price": 49900},
}

@router.message(Command("buy"))
async def cmd_buy(message: Message):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"{t['name']}  {t['price']:,} ₽", callback_data=f"buy_{k}")]
        for k, t in TARIFS.items()
    ])
    await message.answer("Выбери тариф:", reply_markup=kb)

@router.callback_query(F.data.startswith("buy_"))
async def buy_tariff(call: CallbackQuery):
    tariff = call.data.split("_")[1]
    price = TARIFS[tariff]["price"]
    
    payment = Payment.create({
        "amount": {"value": str(price), "currency": "RUB"},
        "confirmation": {"type": "redirect", "return_url": "https://t.me/твой_бот"},
        "capture": True,
        "description": f"Оплата {TARIFS[tariff]['name']}",
        "metadata": {"user_id": str(call.from_user.id)}
    }, uuid.uuid4())

    url = payment.confirmation.confirmation_url
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Оплатить", url=url)],
    ])
    
    await call.message.edit_text(
        f"Тариф: <b>{TARIFS[tariff]['name']}</b>\n"
        f"Цена: <b>{price:,} ₽</b>\n\n"
        f"Нажми кнопку для оплаты:",
        reply_markup=kb,
        parse_mode="HTML"
    )
    await call.answer()
