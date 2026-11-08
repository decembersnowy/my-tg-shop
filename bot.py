import asyncio
import json
import os
from http.server import BaseHTTPRequestHandler, HTTPServer
import threading
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, LabeledPrice, PreCheckoutQuery, ContentType

# === НАСТРОЙКИ ===
BOT_TOKEN = os.environ.get("BOT_TOKEN") or "9111379013:AAGIale1XfxLH-zi14CKI-fvNKHnkeA-HlI"

# ИСПРАВЛЕНО: Обновили версию до v=4 для полного сброса кэша Telegram
WEBAPP_URL = "https://decembersnowy.github.io/my-tg-shop/?v=5" 

PROVIDER_TOKEN_UZS = os.environ.get("PROVIDER_TOKEN_UZS") or "398062629:TEST:999999999_F91D8F69C042267444B74CC0B3C747757EB0E065"

# База данных цен (ID товаров строго совпадать с index.html)
PRODUCTS = {
    1: {"name": "RED STREET SWEATSHIRT", "uzs": 650000},
    2: {"name": "MONTES YELLOW SWEATSHIRT", "uzs": 180000},
    3: {"name": "NAVY LYNX LONG PANTS", "uzs": 290000},
    4: {"name": "BACKPACK PREMIUM", "uzs": 350000},
    5: {"name": "KELME INDOOR FUTSAL WHITE", "uzs": 590000}
}

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# --- Веб-сервер «обманка» для бесплатного тарифа Render ---
class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b'Bot is running perfectly!')

def run_port_listener():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(('0.0.0.0', port), SimpleHTTPRequestHandler)
    server.serve_forever()

# --- Логика Telegram-бота ---
@dp.message(F.text == "/start")
async def start_cmd(message: Message):
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
    
    inline_kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🛍️ Открыть магазин", web_app=WebAppInfo(url=WEBAPP_URL))]
        ]
    )
    
    await message.answer(
        "Добро пожаловать в официальный магазин KELME Uzbekistan! 🐾\n\n"
        "Нажмите на кнопку ниже, чтобы открыть наш каталог одежды, обуви и аксессуаров.",
        reply_markup=inline_kb
    )

# ИСПРАВЛЕНО: Функция теперь идеально принимает новый облегченный формат корзины из index.html
@dp.message(F.web_app_data)
async def process_order(message: Message):
    try:
        # Напрямую вытаскиваем чистую корзину из WebApp
        cart = json.loads(message.web_app_data.data)
        
        prices = []
        description_parts = []

        for p_id, count in cart.items():
            product_id = int(p_id)
            prod = PRODUCTS.get(product_id)
            if prod:
                # Сумма в тийинах для UZS (умножаем на 100)
                prices.append(LabeledPrice(label=f"{prod['name']} x{count}", amount=prod["uzs"] * count * 100))
                description_parts.append(f"{prod['name']} ({count}шт)")

        if not prices:
            await message.answer("Ваша корзина пуста.")
            return
        
        await bot.send_invoice(
            chat_id=message.chat.id,
            title="Оплата заказа Kelme",
            description=", ".join(description_parts),
            payload="kelme_shop_payload",
            provider_token=PROVIDER_TOKEN_UZS,
            currency="UZS",
            prices=prices,
            start_parameter="kelme-shop-order"
        )
    except Exception as e:
        await message.answer(f"Произошла ошибка при формировании счета: {e}")

@dp.pre_checkout_query()
async def pre_checkout_query_handler(pre_checkout_query: PreCheckoutQuery):
    await bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True)

@dp.message(F.content_type == ContentType.SUCCESSFUL_PAYMENT)
async def success_payment(message: Message):
    await message.answer("🎉 Спасибо! Ваша оплата успешно принята. Менеджер свяжется с вами для уточнения доставки.")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    # Запускаем сервер портов в фоновом потоке для Render
    threading.Thread(target=run_port_listener, daemon=True).start()
    # Запускаем самого бота
    asyncio.run(main())
