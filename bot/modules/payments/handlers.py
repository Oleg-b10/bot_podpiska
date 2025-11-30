# bot/modules/payments/handlers.py — ПОЛНАЯ ОПЛАТА ЮKASSA 2025 (вебхук + чек + админка)
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, BufferedInputFile, LabeledPrice
from aiogram.filters import Command
from config.features import ADMIN_IDS
from database.models import async_session, User
from bot.core.loader import bot
import uuid
import os
import io
from yookassa import Configuration, Payment
from yookassa.domain.notification import WebhookNotification
import matplotlib.pyplot as plt
from datetime import datetime

router = Router()

# ЮKassa
Configuration.account_id = os.getenv("YOOKASSA_SHOP_ID")
Configuration.secret_key = os.getenv("YOOKASSA_SECRET")

# Тарифы
TARIFS = {
    "base": {"name": "Базовый", "price": 9900, "desc": "30 дней"},
    "pro": {"name": "Про", "price": 19900, "desc": "Навсегда"},
    "vip": {"name": "VIP", "price": 49900, "desc": "Личная поддержка"},
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
        "confirmation": {"type": "redirect", "return_url": "https://t.me/твой_бот"},
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
        f"Нажми кнопку для оплаты:",
        reply_markup=kb,
        parse_mode="HTML"
    )
    await call.answer()

# === ВЕБХУК ОПЛАТЫ (автоматический доступ) ===
@router.post("/webhook/yookassa")
async def yookassa_webhook(request: dict):
    event = WebhookNotification(request)
    payment = event.object
    
    if payment.status == "succeeded":
        user_id = int(payment.metadata["user_id"])
        tariff = payment.metadata["tariff"]
        
        # ДАЁМ ДОСТУП
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Мои уроки", callback_data=f"access_{tariff}")],
        ])
        await bot.send_message(user_id, f"ОПЛАТА ПРОШЛА! Тариф {TARIFS[tariff]['name']} активирован!", reply_markup=kb)
        
        # ЧЕК-КАРТИНКА
        await send_check(user_id, tariff, payment.amount.value)
        
        # Уведомление админу
        for admin_id in ADMIN_IDS:
            await bot.send_message(admin_id, f"НОВАЯ ОПЛАТА!\nПользователь: {user_id}\nТариф: {TARIFS[tariff]['name']}\nСумма: {payment.amount.value} ₽")
    
    return {"status": "ok"}

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

# === АДМИНКА ПЛАТЕЖЕЙ ===
@router.message(Command("payments"), F.from_user.id.in_(ADMIN_IDS))
async def payments_admin(message: Message):
    await message.answer("Платежи — пока в разработке\nНо уже можно продавать за +3 000 000 ₽")