import asyncio
import json
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, LabeledPrice, PreCheckoutQuery, ContentType

# === НАСТРОЙКИ (Вставьте свои данные) ===
BOT_TOKEN = "9111379013:AAGIale1XfxLH-zi14CKI-fvNKHnkeA-HlI"
# Ссылку на сайт получаем на Шаге 4
WEBAPP_URL = "https://decembersnowy.github.io/my-tg-shop/" 

# Токены платежных систем из BotFather (Шаг 1)
PROVIDER_TOKEN_UZS = "398062629:TEST:999999999_F91D8F69C042267444B74CC0B3C747757EB0E065"
PROVIDER_TOKEN_USD = "1877036958:TEST:5700904b8d9cc34596d3d724baa380cc33d3d18d"

# База данных цен (чтобы проверить честность данных из Web App)
# ID товаров должны строго совпадать с index.html
PRODUCTS = {
    1: {"name": "Худи Базовое", "uzs": 250000, "usd": 20},
    2: {"name": "Кроссовки Street", "uzs": 750000, "usd": 60},
    3: {"name": "Кепка Черная", "uzs": 90000, "usd": 7}
}

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# 1. Приветствие и кнопка открытия магазина
@dp.message(F.text == "/start")
async def start_cmd(message: Message):
    from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, WebAppInfo
    
    # Кнопка под полем ввода
    kb = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="Открыть магазин", web_app=WebAppInfo(url=WEBAPP_URL))]],
        resize_keyboard=True
    )
    await message.answer("Добро пожаловать в наш магазин! Нажмите кнопку ниже, чтобы открыть каталог:", reply_markup=kb)

# 2. Обработка заказа из Web App и выставление счета
@dp.message(F.content_type == ContentType.WEB_APP_DATA)
async def process_order(message: Message):
    try:
        # Принимаем данные от фронтенда
        data = json.loads(message.web_app_data.data)
        currency = data.get("currency") # 'UZS' или 'USD'
        items = data.get("items") # Словарь вида {"1": 2} (ID товара: количество)
        
        prices = []
        total_amount = 0
        description_parts = []

        for p_id, count in items.items():
            prod = PRODUCTS.get(int(p_id))
            if prod:
                price_each = prod["uzs"] if currency == "UZS" else prod["usd"]
                # Для Telegram Payments: UZS указывается в минимальных единицах (тийнах), поэтому умножаем на 100.
                # Для USD также умножаем на 100 (центы).
                prices.append(LabeledPrice(label=f"{prod['name']} x{count}", amount=price_each * count * 100))
                description_parts.append(f"{prod['name']} ({count}шт)")

        # Формируем и отправляем инвойс для оплаты картой
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

# 3. Предварительное подтверждение платежа (обязательно для Telegram)
@dp.pre_checkout_query()
async def pre_checkout_query_handler(pre_checkout_query: PreCheckoutQuery):
    await bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True)

# 4. Уведомление об успешной оплате
@dp.message(F.content_type == ContentType.SUCCESSFUL_PAYMENT)
async def success_payment(message: Message):
    await message.answer("🎉 Спасибо! Ваша оплата успешно принята. Менеджер свяжется с вами для уточнения доставки.")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
