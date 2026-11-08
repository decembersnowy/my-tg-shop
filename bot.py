import asyncio
import json
import os
from http.server import BaseHTTPRequestHandler, HTTPServer
import threading
import urllib.parse
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, LabeledPrice, PreCheckoutQuery, ContentType

# === НАСТРОЙКИ ===
BOT_TOKEN = os.environ.get("BOT_TOKEN") or "9111379013:AAHUgMUW3Iccs33cOG7OWX4BKb2usfYAxaA"
# Ссылка на твою витрину с новой версией v=200 для полного сброса кэша Telegram
WEBAPP_URL = "https://decembersnowy.github.io/my-tg-shop/?v=200" 
PROVIDER_TOKEN_UZS = os.environ.get("PROVIDER_TOKEN_UZS") or "398062629:TEST:999999999_F91D8F69C042267444B74CC0B3C747757EB0E065"

# База данных цен
PRODUCTS = {
    1: {"name": "RED STREET SWEATSHIRT", "uzs": 650000},
    2: {"name": "MONTES YELLOW SWEATSHIRT", "uzs": 180000},
    3: {"name": "NAVY LYNX LONG PANTS", "uzs": 290000},
    4: {"name": "BACKPACK PREMIUM", "uzs": 350000},
}

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# --- Полноценный API-сервер для связи с Mini App витриной ---
class WebAppAPIServer(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def do_POST(self):
        if self.path == '/create_invoice':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))
            
            cart = data.get("cart", {})
            chat_id = data.get("chat_id")
            
            prices = []
            description_parts = []
            
            for p_id, count in cart.items():
                prod = PRODUCTS.get(int(p_id))
                if prod:
                    prices.append(LabeledPrice(label=f"{prod['name']} x{count}", amount=prod["uzs"] * count * 100))
                    description_parts.append(f"{prod['name']} ({count}шт)")
            
            loop = asyncio.get_event_loop()
            try:
                # Генерируем официальную платежную ссылку Telegram
                invoice_link = loop.run_until_complete(bot.create_invoice_link(
                    title="Оплата заказа Kelme",
                    description=", ".join(description_parts),
                    payload="kelme_shop_payload",
                    provider_token=PROVIDER_TOKEN_UZS,
                    currency="UZS",
                    prices=prices
                ))
                
                response = {"ok": True, "invoice_link": invoice_link}
                status_code = 200
            except Exception as e:
                response = {"ok": False, "error": str(e)}
                status_code = 500

            self.send_response(status_code)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(response).encode('utf-8'))

    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-Type', 'text/plain')
        self.end_headers()
        self.wfile.write(b'Bot API Server is running perfectly!')

def run_port_listener():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(('0.0.0.0', port), WebAppAPIServer)
    server.serve_forever()

# --- Логика бота ---
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

@dp.pre_checkout_query()
async def pre_checkout_query_handler(pre_checkout_query: PreCheckoutQuery):
    await bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True)

@dp.message(F.content_type == ContentType.SUCCESSFUL_PAYMENT)
async def success_payment(message: Message):
    await message.answer("🎉 Спасибо! Ваша оплата успешно принята. Менеджер свяжется с вами для уточнения доставки.")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    threading.Thread(target=run_port_listener, daemon=True).start()
    asyncio.run(main())
