# bot/modules/payments/handlers.py — ОПЛАТА С ВЕБХУКОМ НА LOCAlHOST (2025)
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, BufferedInputFile
from aiogram.filters import Command
from config.features import ADMIN_IDS
from yookassa import Configuration, Payment
from yookassa.domain.notification import WebhookNotification
from fastapi import Request, Response
import uuid
import io
import matplotlib.pyplot as plt
from datetime import datetime
from bot.core.loader import bot
import os

router = Router()

# ЮKassa
Configuration.account_id = os.getenv("YOOKASSA_SHOP_ID")
Configuration.secret_key = os.getenv("YOOKASSA_SECRET")

TARIFS = {
    "base": {"name": "Базовый", "price": 9900},
    "pro": {"name": "Про", "price": 19900},
    "vip": {"name": "VIP", "price": 49900},
}

# === КОМАНДА /buy ===
@router.message(Command("buy"))
async def cmd_buy(message: Message):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"{t['name']} — {t['price']:,} ₽", callback_data=f"buy_{k}")]
        for k, t in TARIFS.items()
    ])
    await message.answer("Выбери тариф:", reply_markup=kb)

# === ОПЛАТА ===
@router.callback_query(F.data.startswith("buy_"))
async def buy_tariff(call: CallbackQuery):
    tariff = call.data.split("_")[1]
    price = TARIFS[tariff]["price"]
    
    payment = Payment.create({
        "amount": {"value": str(price), "currency": "RUB"},
        "confirmation": {"type": "redirect", "return_url": f"https://t.me/{(await bot.get_me()).username}"},
        "capture": True,
        "description": f"Оплата {TARIFS[tariff]['name']}",
        "metadata": {"user_id": str(call.from_user.id), "tariff": tariff}
    }, uuid.uuid4())

    url = payment.confirmation.confirmation_url
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Оплатить", url=url)],
    ])
    
    await call.message.edit_text(
        f"Тариф: <b>{TARIFS[tariff]['name']}</b>\n"
        f"Цена: <b>{price:,} ₽</b>\n\n"
        f"Нажми для оплаты:",
        reply_markup=kb,
        parse_mode="HTML"
    )
    await call.answer()

# === ВЕБХУК — МОЛНИЕНОСНЫЙ ДОСТУП ===
@router.post("/webhook/yookassa")
async def yookassa_webhook(request: Request):
    data = await request.json()
    try:
        event = WebhookNotification(data)
        if event.event == "payment.succeeded":
            payment = event.object
            user_id = int(payment.metadata["user_id"])
            tariff = payment.metadata["tariff"]
            
            # Мгновенный доступ
            kb = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="Мои уроки", callback_data=f"access_{tariff}")],
            ])
            await bot.send_message(user_id, f"ОПЛАТА ПРОШЛА!\nТариф <b>{TARIFS[tariff]['name']}</b> активирован!", reply_markup=kb, parse_mode="HTML")
            
            # Чек
            await send_check(user_id, tariff, payment.amount.value)
            
            # Админу
            for admin in ADMIN_IDS:
                await bot.send_message(admin, f"НОВАЯ ОПЛАТА!\nID: {user_id}\nТариф: {TARIFS[tariff]['name']}\nСумма: {payment.amount.value} ₽")
    except:
        pass
    return Response(content="ok", status_code=200)

# === ЧЕК-КАРТИНКА ===
async def send_check(user_id: int, tariff: str, amount: str):
    fig, ax = plt.subplots(figsize=(8, 6))
    ax.text(0.5, 0.8, "ОПЛАТА ПРОШЛА!", fontsize=22, ha='center', fontweight='bold', color="#00ff88")
    ax.text(0.5, 0.6, f"Тариф: {TARIFS[tariff]['name']}", fontsize=18, ha='center')
    ax.text(0.5, 0.5, f"Сумма: {amount} ₽", fontsize=18, ha='center')
    ax.text(0.5, 0.4, f"Дата: {datetime.now():%d.%m.%Y %H:%M}", fontsize=14, ha='center')
    ax.axis('off')

    buffer = io.BytesIO()
    plt.savefig(buffer, format='png', bbox_inches='tight')
    buffer.seek(0)
    plt.close(fig)

    photo = BufferedInputFile(buffer.read(), filename="check.png")
    await bot.send_photo(user_id, photo, caption="Твой чек! Сохрани")