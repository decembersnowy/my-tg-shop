import asyncio
import json
import os
from http.server import BaseHTTPRequestHandler, HTTPServer
import threading
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, PreCheckoutQuery, ContentType

# === НАСТРОЙКИ ===
BOT_TOKEN = os.environ.get("BOT_TOKEN") or "9111379013:AAHUgMUW3Iccs33cOG7OWX4BKb2usfYAxaA"
WEBAPP_URL = "https://decembersnowy.github.io/my-tg-shop/?v=103" 
PROVIDER_TOKEN_UZS = os.environ.get("PROVIDER_TOKEN_UZS") or "398062629:TEST:999999999_F91D8F69C042267444B74CC0B3C747757EB0E065"

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b'Bot is running perfectly!')

def run_port_listener():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(('0.0.0.0', port), SimpleHTTPRequestHandler)
    server.serve_forever()

@dp.message(F.text == "/start")
async def start_cmd(message: Message):
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
    inline_kb = InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="🛍️ Открыть магазин", web_app=WebAppInfo(url=WEBAPP_URL))]]
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
