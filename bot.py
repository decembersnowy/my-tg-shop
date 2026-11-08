import asyncio
import json
import os
from http.server import BaseHTTPRequestHandler, HTTPServer
import threading
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, LabeledPrice, PreCheckoutQuery, ContentType

# === НАСТРОЙКИ (Вставьте свои данные) ===
BOT_TOKEN = "9111379013:AAGIale1XfxLH-zi14CKI-fvNKHnkeA-HlI"
WEBAPP_URL = "https://decembersnowy.github.io/my-tg-shop/" 

PROVIDER_TOKEN_UZS = "398062629:TEST:999999999_F91D8F69C042267444B74CC0B3C747757EB0E065"
PROVIDER_TOKEN_USD = "1877036958:TEST:5700904b8d9cc34596d3d724baa380cc33d3d18d"

# База данных цен (ID товаров должны строго совпадать с index.html)
PRODUCTS = {
    { id: 1, name: "RED STREET SWEATSHIRT", price_uzs: 650000, price_usd: 50, img: "https://kelme.com/cdn/shop/files/11425.jpg?v=1748001678&width=1000" },
    { id: 2, name: "MONTES YELLOW SWEATSHIRT", price_uzs: 180000, price_usd: 15, img: "https://kelme.com/cdn/shop/files/9569.jpg?v=1748005352&width=1000" },
    { id: 3, name: "NAVY LYNX LONG PANTS", price_uzs: 290000, price_usd: 22, img: "https://kelme.com/cdn/shop/files/3085.jpg?v=1748001775&width=600" },
    { id: 4, name: "BACKPACK", price_uzs: 350000, price_usd: 28, img: "https://kelme.com/cdn/shop/files/4603.jpg?v=1748003643&width=700" }
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
    from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, WebAppInfo
    kb = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="Открыть магазин", web_app=WebAppInfo(url=WEBAPP_URL))]],
        resize_keyboard=True
    )
    await message.answer("Добро пожаловать в наш магазин! Нажмите кнопку ниже, чтобы открыть каталог:", reply_markup=kb)

@dp.message(F.content_type == ContentType.WEB_APP_DATA)
async def process_order(message: Message):
    try:
        data = json.loads(message.web_app_data.data)
        currency = data.get("currency")
        items = data.get("items")
        
        prices = []
        description_parts = []

        for p_id, count in items.items():
            prod = PRODUCTS.get(int(p_id))
            if prod:
                price_each = prod["uzs"] if currency == "UZS" else prod["usd"]
                prices.append(LabeledPrice(label=f"{prod['name']} x{count}", amount=price_each * count * 100))
                description_parts.append(f"{prod['name']} ({count}шт)")

        provider_token = PROVIDER_TOKEN_UZS if currency == "UZS" else PROVIDER_TOKEN_USD
        
        await bot.send_invoice(
            chat_id=message.chat.id,
            title="Оплата заказа",
            description=", ".join(description_parts),
            payload="shop_order_payload",
            provider_token=provider_token,
            currency=currency,
            prices=prices,
            start_parameter="shop-order"
        )
    except Exception as e:
        await message.answer("Произошла ошибка при формировании счета.")

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
