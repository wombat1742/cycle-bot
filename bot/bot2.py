import logging
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext, ConversationHandler
from datetime import datetime
import json
import os

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Состояния для ConversationHandler
SELECTING_CATEGORY, VIEWING_PRODUCT, CART, CHECKOUT = range(4)

# Данные о велосипедах (в реальном проекте это была бы БД)
BIKES_DATA = {
    'folding': {
        'name': '📦 Складные велосипеды',
        'bikes': [
            {'id': 1, 'name': 'Stels Folding Pro', 'price': 15000, 'description': 'Легкий складной велосипед для города'},
            {'id': 2, 'name': 'Forward Compact', 'price': 12000, 'description': 'Компактный и удобный'},
        ]
    },
    'mountain': {
        'name': '🏔️ Горные велосипеды',
        'bikes': [
            {'id': 3, 'name': 'GT Aggressor Pro', 'price': 35000, 'description': 'Профессиональный горный велосипед'},
            {'id': 4, 'name': 'Trek Marlin 5', 'price': 28000, 'description': 'Надежный для трейлов'},
        ]
    },
    'hybrid': {
        'name': '🚴 Гибридные велосипеды',
        'bikes': [
            {'id': 5, 'name': 'Scott Sub Cross', 'price': 32000, 'description': 'Универсальный для города и легкого бездорожья'},
            {'id': 6, 'name': 'Cannondale Quick', 'price': 25000, 'description': 'Комфортный и быстрый'},
        ]
    },
    'road': {
        'name': '🏁 Шоссейные велосипеды',
        'bikes': [
            {'id': 7, 'name': 'Specialized Allez', 'price': 45000, 'description': 'Легкий и быстрый шоссейник'},
            {'id': 8, 'name': 'Bianchi Via Nirone', 'price': 52000, 'description': 'Классика итальянского бренда'},
        ]
    }
}

# Хранилище корзин пользователей (в реальном проекте - БД)
user_carts = {}

async def start(update: Update, context: CallbackContext) -> int:
    """Начало работы с ботом - главное меню"""
    user = update.message.from_user
    logger.info(f"User {user.first_name} started the conversation")
    
    # Инициализируем корзину пользователя
    user_carts[user.id] = []
    
    keyboard = [
        [KeyboardButton("📦 Складные"), KeyboardButton("🏔️ Горные")],
        [KeyboardButton("🚴 Гибридные"), KeyboardButton("🏁 Шоссейные")],
        [KeyboardButton("🛒 Корзина"), KeyboardButton("ℹ️ О нас")]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
    await update.message.reply_text(
        "🚴‍♂️ Добро пожаловать в магазин велосипедов!\n\n"
        "Выберите категорию велосипедов:",
        reply_markup=reply_markup
    )
    
    return SELECTING_CATEGORY

async def handle_category_selection(update: Update, context: CallbackContext) -> int:
    """Обработка выбора категории"""
    text = update.message.text
    user = update.message.from_user
    
    category_map = {
        "📦 Складные": "folding",
        "🏔️ Горные": "mountain", 
        "🚴 Гибридные": "hybrid",
        "🏁 Шоссейные": "road"
    }
    
    if text in category_map:
        category = category_map[text]
        context.user_data['current_category'] = category
        
        # Показываем велосипеды в выбранной категории
        bikes = BIKES_DATA[category]['bikes']
        
        keyboard = []
        for bike in bikes:
            keyboard.append([KeyboardButton(f"🚲 {bike['name']} - {bike['price']}₽")])
        
        keyboard.append([KeyboardButton("⬅️ Назад"), KeyboardButton("🛒 Корзина")])
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        
        await update.message.reply_text(
            f"🏷️ {BIKES_DATA[category]['name']}:\n\n"
            "Выберите велосипед для просмотра:",
            reply_markup=reply_markup
        )
return VIEWING_PRODUCT
    
    elif text == "🛒 Корзина":
        return await show_cart(update, context)
    elif text == "ℹ️ О нас":
        await update.message.reply_text(
            "🏪 Магазин 'BikeShop'\n\n"
            "📞 Телефон: +7 (999) 123-45-67\n"
            "📍 Адрес: г. Москва, ул. Велосипедная, 1\n"
            "⏰ Время работы: 10:00 - 20:00\n\n"
            "Лучшие велосипеды по доступным ценам!"
        )
        return SELECTING_CATEGORY
    
    return SELECTING_CATEGORY

async def handle_product_selection(update: Update, context: CallbackContext) -> int:
    """Обработка выбора конкретного велосипеда"""
    text = update.message.text
    user = update.message.from_user
    
    if text == "⬅️ Назад":
        return await start(update, context)
    elif text == "🛒 Корзина":
        return await show_cart(update, context)
    
    # Ищем выбранный велосипед
    current_category = context.user_data.get('current_category', 'folding')
    bikes = BIKES_DATA[current_category]['bikes']
    
    selected_bike = None
    for bike in bikes:
        if f"🚲 {bike['name']} - {bike['price']}₽" in text:
            selected_bike = bike
            break
    
    if selected_bike:
        context.user_data['selected_bike'] = selected_bike
        
        keyboard = [
            [KeyboardButton("✅ Добавить в корзину")],
            [KeyboardButton("⬅️ Назад к категориям"), KeyboardButton("🛒 Корзина")]
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        
        await update.message.reply_text(
            f"🚲 {selected_bike['name']}\n\n"
            f"📝 {selected_bike['description']}\n"
            f"💰 Цена: {selected_bike['price']}₽\n\n"
            f"Хотите добавить этот велосипед в корзину?",
            reply_markup=reply_markup
        )
        
        return VIEWING_PRODUCT
    
    return VIEWING_PRODUCT

async def add_to_cart(update: Update, context: CallbackContext) -> int:
    """Добавление товара в корзину"""
    user = update.message.from_user
    selected_bike = context.user_data.get('selected_bike')
    
    if selected_bike:
        user_carts[user.id].append(selected_bike)
        await update.message.reply_text(f"✅ {selected_bike['name']} добавлен в корзину!")
    
    return await handle_category_selection(update, context)

async def show_cart(update: Update, context: CallbackContext) -> int:
    """Показать корзину пользователя"""
    user = update.message.from_user
    cart = user_carts.get(user.id, [])
    
    if not cart:
        keyboard = [[KeyboardButton("⬅️ Назад к категориям")]]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text(
            "🛒 Ваша корзина пуста",
            reply_markup=reply_markup
        )
        return SELECTING_CATEGORY
    
    total = sum(item['price'] for item in cart)
    cart_text = "🛒 Ваша корзина:\n\n"
    
    for i, item in enumerate(cart, 1):
        cart_text += f"{i}. {item['name']} - {item['price']}₽\n"
    
    cart_text += f"\n💰 Итого: {total}₽"
    
    keyboard = [
        [KeyboardButton("✅ Оформить заказ")],
        [KeyboardButton("🗑️ Очистить корзину"), KeyboardButton("⬅️ Назад к категориям")]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
    await update.message.reply_text(cart_text, reply_markup=reply_markup)
    
    return CART

async def handle_cart_actions(update: Update, context: CallbackContext) -> int:
    """Обработка действий в корзине"""
    text = update.message.text
    user = update.message.from_user
    
    if text == "✅ Оформить заказ":
        return await checkout(update, context)
    elif text == "🗑️ Очистить корзину":
        user_carts[user.id] = []
        await update.message.reply_text("🗑️ Корзина очищена!")
        return await start(update, context)
    elif text == "⬅️ Назад к категориям":
        return await start(update, context)
    
    return CART

async def checkout(update: Update, context: CallbackContext) -> int:
"""Оформление заказа"""
    user = update.message.from_user
    cart = user_carts.get(user.id, [])
    
    if not cart:
        await update.message.reply_text("Корзина пуста!")
        return await start(update, context)
    
    total = sum(item['price'] for item in cart)
    
    # В реальном проекте здесь была бы логика оформления заказа
    order_text = f"📦 Заказ оформлен!\n\n"
    for item in cart:
        order_text += f"• {item['name']} - {item['price']}₽\n"
    order_text += f"\n💰 Итого: {total}₽\n\n"
    order_text += "📞 Наш менеджер свяжется с вами в ближайшее время для подтверждения заказа!"
    
    # Очищаем корзину после оформления
    user_carts[user.id] = []
    
    keyboard = [[KeyboardButton("🔄 Новый заказ")]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
    await update.message.reply_text(order_text, reply_markup=reply_markup)
    
    return SELECTING_CATEGORY

async def cancel(update: Update, context: CallbackContext) -> int:
    """Отмена диалога"""
    user = update.message.from_user
    logger.info(f"User {user.first_name} canceled the conversation.")
    await update.message.reply_text(
        'До свидания! Если захотите снова посмотреть велосипеды, напишите /start',
        reply_markup=ReplyKeyboardMarkup([['/start']], resize_keyboard=True)
    )
    
    return ConversationHandler.END

def main() -> None:
    """Запуск бота"""
    # Токен бота (замени на свой)
    TOKEN = "YOUR_TELEGRAM_BOT_TOKEN"
    
    # Создаем Application
    application = Application.builder().token(TOKEN).build()
    
    # Настраиваем ConversationHandler
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            SELECTING_CATEGORY: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_category_selection)
            ],
            VIEWING_PRODUCT: [
                MessageHandler(filters.Regex("^✅ Добавить в корзину$"), add_to_cart),
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_product_selection)
            ],
            CART: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_cart_actions)
            ],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )
    
    application.add_handler(conv_handler)
    
    # Запускаем бота
    print("Бот запущен...")
    application.run_polling()

if __name__ == '__main__':
    main()
