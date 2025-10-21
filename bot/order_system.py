import logging
from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from datetime import datetime
import random

logger = logging.getLogger(__name__)

router = Router()

# Временные хранилища (в продакшене - БД)
user_carts = {}
user_orders = {}

class OrderStates(StatesGroup):
    waiting_for_phone = State()
    waiting_for_address = State()
    choosing_delivery = State()
    waiting_for_promo = State()

# 4. СИСТЕМА УВЕДОМЛЕНИЙ ДЛЯ ПОЛЬЗОВАТЕЛЕЙ
async def notify_user_about_order_status(bot: Bot, order_data: dict):
    """Уведомление пользователя о статусе заказа"""
    user_id = order_data['user_id']
    
    status_messages = {
        "Новый": "🆕 Ваш заказ принят в обработку",
        "В работе": "👨‍🍳 Ваш заказ готовится", 
        "Готов": "✅ Ваш заказ готов к выдаче",
        "В пути": "🚗 Ваш заказ в пути к вам",
        "Доставлен": "🎉 Заказ доставлен! Спасибо за покупку!",
        "Отменен": "❌ Заказ отменен"
    }
    
    message = status_messages.get(order_data['status'], "ℹ️ Статус вашего заказа обновлен")
    
    notification_text = (
        f"{message}\n\n"
        f"🎫 Заказ: #{order_data['id']}\n"
        f"📊 Статус: {order_data['status']}\n"
        f"💵 Сумма: {order_data['total']}₽\n"
    )
    
    if order_data['status'] == "Готов" and order_data['delivery_type'] == "Самовывоз":
        notification_text += "\n🏪 Можете забирать заказ по адресу:\nг. Москва, ул. Велосипедная, 1\n\n⏰ Часы работы: 10:00-20:00"
    
    elif order_data['status'] == "В пути":
        notification_text += f"\n🚗 Курьер уже в пути!\n📞 Телефон курьера: +7 (999) 765-43-21"
    
    keyboard = [
        [InlineKeyboardButton(text="📦 Подробнее о заказе", callback_data=f"order_status_{order_data['id']}")],
        [InlineKeyboardButton(text="📞 Связаться с нами", callback_data="support")]
    ]
    
    try:
        await bot.send_message(
            chat_id=user_id,
            text=notification_text,
            reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
        )
        logger.info(f"✅ Уведомление отправлено пользователю {user_id} о заказе {order_data['id']}")
    except Exception as e:
        logger.error(f"❌ Ошибка отправки уведомления пользователю: {e}")

async def notify_user_about_promotion(bot: Bot, user_id: int, promotion_data: dict):
    """Уведомление о акциях и специальных предложениях"""
    promotion_text = (
        f"🎁 **Специальное предложение!**\n\n"
        f"{promotion_data['title']}\n\n"
        f"{promotion_data['description']}\n\n"
        f"⏰ {promotion_data['duration']}"
    )
    
    keyboard = [
        [InlineKeyboardButton(text="🛒 Посмотреть товары", callback_data="catalog")],
        [InlineKeyboardButton(text="🎁 Подробнее об акции", callback_data=f"promo_{promotion_data['id']}")]
    ]
    
    try:
        await bot.send_message(
            chat_id=user_id,
            text=promotion_text,
            reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
        )
    except Exception as e:
        logger.error(f"❌ Ошибка отправки промо-уведомления: {e}")

# Автоматическое обновление статусов заказов (заглушка)
async def simulate_order_progress(bot: Bot, order_id: str):
    """Симуляция прогресса заказа для демонстрации"""
    if order_id not in user_orders:
        return
    
    order = user_orders[order_id]
    status_flow = ["Новый", "В работе", "Готов", "В пути", "Доставлен"]
    
    current_index = status_flow.index(order['status']) if order['status'] in status_flow else 0
    
    if current_index < len(status_flow) - 1:
        # Обновляем статус
        new_status = status_flow[current_index + 1]
        user_orders[order_id]['status'] = new_status
        
        # Отправляем уведомление пользователю
        await notify_user_about_order_status(bot, user_orders[order_id])
        
        logger.info(f"🔄 Статус заказа {order_id} изменен на: {new_status}")

# 5. СИСТЕМА АКЦИЙ И ПРОМОКОДОВ (оставляем, это полезно)
@router.callback_query(F.data == "promo")
async def enter_promo(callback: CallbackQuery, state: FSMContext):
    """Ввод промокода"""
    await callback.message.edit_text(
        "🎁 **Введите промокод:**\n\n"
        "Доступные промокоды:\n"
        "• WELCOME10 - 10% скидка\n"
        "• BIKE2024 - 15% на велосипеды\n"
        "• FREEDELIVERY - бесплатная доставка",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="❌ Отмена", callback_data="cart")]
        ])
    )
    await state.set_state(OrderStates.waiting_for_promo)

@router.message(OrderStates.waiting_for_promo)
async def apply_promo(message: Message, state: FSMContext):
    """Применение промокода"""
    promo = message.text.upper().strip()
    promocodes = {
        "WELCOME10": {"discount": 10, "type": "percent", "message": "🎉 10% скидка на весь заказ!"},
        "BIKE2024": {"discount": 15, "type": "percent", "message": "🚴 15% скидка на велосипеды!"},
        "FREEDELIVERY": {"discount": 0, "type": "free_delivery", "message": "🚗 Бесплатная доставка активирована!"}
    }
    
    if promo in promocodes:
        promo_data = promocodes[promo]
        await state.update_data(promo=promo, promo_data=promo_data)
        await message.answer(f"✅ {promo_data['message']}")
        
        # Показываем обновленную корзину
        await message.answer("🛒 Обновите корзину для применения скидки")
        
    else:
        await message.answer("❌ Неверный промокод. Попробуйте еще раз:")
    
    await state.clear()

# 6. СИСТЕМА УВЕДОМЛЕНИЙ О АКЦИЯХ (вместо отзывов)
@router.callback_query(F.data == "subscribe_promo")
async def subscribe_to_promotions(callback: CallbackQuery):
    """Подписка на акции и уведомления"""
    user_id = callback.from_user.id
    
    # Здесь можно сохранить в БД подписку пользователя
    await callback.message.edit_text(
        "🔔 **Вы подписаны на уведомления!**\n\n"
        "Теперь вы будете первыми узнавать о:\n"
        "• 🎁 Скидках и акциях\n"
        "• 🚴 Новых поступлениях\n"
        "• ⚡ Специальных предложениях\n\n"
        "Не пропустите ничего важного!",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🛒 Перейти в каталог", callback_data="catalog")],
            [InlineKeyboardButton(text="📋 Главное меню", callback_data="main_menu")]
        ])
    )

@router.callback_query(F.data.startswith("promo_"))
async def show_promotion_details(callback: CallbackQuery):
    """Показать детали акции"""
    promo_id = callback.data.split('_')[1]
    
    promotions = {
        "bike2024": {
            "title": "🚴 СКИДКА 15% НА ВЕЛОСИПЕДЫ",
            "description": "Только в январе специальное предложение на все модели велосипедов!",
            "duration": "Акция действует до 31.01.2024"
        },
        "welcome": {
            "title": "🎁 10% СКИДКА ДЛЯ НОВЫХ КЛИЕНТОВ",
            "description": "Приветственная скидка на первый заказ!",
            "duration": "Постоянная акция"
        }
    }
    
    promo = promotions.get(promo_id, {
        "title": "🎁 Акция",
        "description": "Специальное предложение",
        "duration": "Ограниченное время"
    })
    
    await callback.message.edit_text(
        f"{promo['title']}\n\n"
        f"{promo['description']}\n\n"
        f"⏰ {promo['duration']}\n\n"
        f"💡 Используйте промокод при оформлении заказа",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🛒 Перейти в каталог", callback_data="catalog")],
            [InlineKeyboardButton(text="🎁 Ввести промокод", callback_data="promo")],
            [InlineKeyboardButton(text="📋 Главное меню", callback_data="main_menu")]
        ])
    )

# 7. СИСТЕМА ДОСТАВКИ И САМОВЫВОЗА (оставляем, это важно)
@router.callback_query(F.data == "checkout")
async def choose_delivery(callback: CallbackQuery, state: FSMContext):
    """Выбор способа доставки"""
    user_id = callback.from_user.id
    cart = user_carts.get(user_id, {})
    
    if not cart:
        await callback.message.edit_text(
            "🛒 Ваша корзина пуста",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🛒 К каталогу", callback_data="catalog")],
                [InlineKeyboardButton(text="📋 Главное меню", callback_data="main_menu")]
            ])
        )
        return
    
    keyboard = [
        [InlineKeyboardButton(text="🚗 Доставка курьером (+300₽)", callback_data="delivery_courier")],
        [InlineKeyboardButton(text="🏪 Самовывоз из магазина (бесплатно)", callback_data="delivery_pickup")],
        [InlineKeyboardButton(text="❌ Отмена", callback_data="cart")]
    ]
    
    await callback.message.edit_text(
        "🚚 **Выберите способ получения**\n\n"
        "• 🚗 Доставка - 300₽ (2-3 часа)\n"
        "• 🏪 Самовывоз - бесплатно (готов через 1 час)\n\n"
        "📍 Адрес магазина: г. Москва, ул. Велосипедная, 1",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
    )
    await state.set_state(OrderStates.choosing_delivery)

@router.callback_query(F.data.startswith("delivery_"))
async def handle_delivery_choice(callback: CallbackQuery, state: FSMContext):
    """Обработка выбора доставки"""
    delivery_type = callback.data.split('_')[1]
    
    delivery_info = {
        "courier": {"name": "Доставка курьером", "price": 300},
        "pickup": {"name": "Самовывоз", "price": 0}
    }
    
    delivery_data = delivery_info.get(delivery_type, {"name": "Не указано", "price": 0})
    await state.update_data(delivery_type=delivery_data['name'], delivery_price=delivery_data['price'])
    
    await callback.message.edit_text(
        "📞 **Введите ваш номер телефона для связи:**",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="❌ Отмена", callback_data="cart")]
        ])
    )
    await state.set_state(OrderStates.waiting_for_phone)

# ОБНОВЛЕННАЯ ФУНКЦИЯ ОФОРМЛЕНИЯ ЗАКАЗА С УВЕДОМЛЕНИЯМИ
@router.message(OrderStates.waiting_for_phone)
async def handle_phone(message: Message, state: FSMContext):
    """Обработка номера телефона"""
    await state.update_data(phone=message.text)
    
    data = await state.get_data()
    delivery_type = data.get('delivery_type', '')
    
    if delivery_type == "Самовывоз":
        # Для самовывоза не нужен адрес
        await complete_order(message, state)
    else:
        # Для доставки запрашиваем адрес
        await message.answer(
            "📍 **Введите адрес доставки:**\n\n"
            "Укажите улицу, дом, квартиру:",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="❌ Отмена", callback_data="cart")]
            ])
        )
        await state.set_state(OrderStates.waiting_for_address)

@router.message(OrderStates.waiting_for_address)
async def handle_address(message: Message, state: FSMContext, bot: Bot):
    """Обработка адреса и завершение заказа"""
    await state.update_data(address=message.text)
    await complete_order(message, state, bot)

async def complete_order(message: Message, state: FSMContext, bot: Bot = None):
    """Завершение оформления заказа"""
    user_id = message.from_user.id
    data = await state.get_data()
    
    # Создаем заказ
    order_id = f"{random.randint(1000, 9999)}"
    order_data = {
        "id": order_id,
        "user_id": user_id,
        "user_name": message.from_user.first_name,
        "phone": data['phone'],
        "address": data.get('address', 'Самовывоз'),
        "delivery_type": data.get('delivery_type', 'Самовывоз'),
        "delivery_price": data.get('delivery_price', 0),
        "status": "Новый",
        "created_at": datetime.now().strftime("%d.%m.%Y %H:%M"),
        "items": [],
        "total": 0
    }
    
    # Добавляем товары
    products = {
        1: {"name": "Горный велосипед X1", "price": 25000},
        2: {"name": "Городской велосипед", "price": 18000},
    }
    
    cart = user_carts.get(user_id, {})
    items_total = 0
    
    for product_id, quantity in cart.items():
        product = products.get(product_id, {"name": f"Товар #{product_id}", "price": 0})
        item_total = product['price'] * quantity
        items_total += item_total
        
        order_data['items'].append({
            "name": product['name'],
            "price": product['price'],
            "quantity": quantity,
            "total": item_total
        })
    
    # Применяем промокод если есть
    promo_data = data.get('promo_data', {})
    if promo_data:
        if promo_data['type'] == 'percent':
            discount = items_total * promo_data['discount'] / 100
            items_total -= discount
        elif promo_data['type'] == 'free_delivery':
            order_data['delivery_price'] = 0
    
    order_data['total'] = items_total + order_data['delivery_price']
    
    # Сохраняем заказ
    user_orders[order_id] = order_data
    
    # Очищаем корзину
    user_carts[user_id] = {}
    
    # Отправляем первое уведомление пользователю
    if bot:
        await notify_user_about_order_status(bot, order_data)
    
    # Подтверждение пользователю
    confirmation_text = (
        f"✅ **Заказ оформлен!**\n\n"
        f"🎫 Номер заказа: #{order_id}\n"
        f"📞 Телефон: {data['phone']}\n"
        f"🚚 Способ: {order_data['delivery_type']}\n"
    )
    
    if order_data['delivery_type'] != 'Самовывоз':
        confirmation_text += f"📍 Адрес: {data['address']}\n"
    else:
        confirmation_text += "📍 Самовывоз: г. Москва, ул. Велосипедная, 1\n"
    
    confirmation_text += (
        f"💵 Сумма: {order_data['total']}₽\n\n"
        f"⏰ {order_data['delivery_type']} - готов через 1-2 часа\n"
        f"💳 Оплата при получении\n\n"
        f"📞 Для связи: +7 (999) 123-45-67\n\n"
        f"🔔 Вы будете получать уведомления о статусе заказа!"
    )
    
    keyboard = [
        [InlineKeyboardButton(text="📦 Отследить заказ", callback_data=f"order_status_{order_id}")],
        [InlineKeyboardButton(text="🔔 Подписаться на акции", callback_data="subscribe_promo")],
        [InlineKeyboardButton(text="📋 Главное меню", callback_data="main_menu")]
    ]
    
    await message.answer(confirmation_text, reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard))
    await state.clear()

# ОБНОВЛЕННАЯ ФУНКЦИЯ СТАТУСА ЗАКАЗА
@router.callback_query(F.data.startswith("order_status_"))
async def check_order_status(callback: CallbackQuery, bot: Bot):
    """Проверка статуса заказа с возможностью симуляции прогресса"""
    order_id = callback.data.split('_')[2]
    
    if order_id not in user_orders:
        await callback.message.edit_text(
            "❌ Заказ не найден",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="📦 Мои заказы", callback_data="orders")],
                [InlineKeyboardButton(text="📋 Главное меню", callback_data="main_menu")]
            ])
        )
        return
    
    order = user_orders[order_id]
    
    # Создаем клавиатуру с действиями
    keyboard = []
    
    # Если заказ не завершен, добавляем кнопку "Обновить статус" для демо
    if order['status'] != "Доставлен":
        keyboard.append([InlineKeyboardButton(text="🔄 Обновить статус (демо)", callback_data=f"simulate_progress_{order_id}")])
    
    keyboard.extend([
        [InlineKeyboardButton(text="📞 Связаться с нами", callback_data="support")],
        [InlineKeyboardButton(text="📦 Все заказы", callback_data="orders")],
        [InlineKeyboardButton(text="📋 Главное меню", callback_data="main_menu")]
    ])
    
    status_info = {
        "Новый": "🆕 Заказ принят, начинаем сборку",
        "В работе": "👨‍🍳 Ваш заказ собирается",
        "Готов": "✅ Заказ готов к выдаче/отправке", 
        "В пути": "🚗 Курьер в пути к вам",
        "Доставлен": "🎉 Заказ доставлен! Спасибо!"
    }
    
    status_description = status_info.get(order['status'], "ℹ️ Информация о заказе")
    
    order_text = (
        f"📦 **Заказ #{order_id}**\n\n"
        f"📊 Статус: {order['status']}\n"
        f"{status_description}\n\n"
        f"📅 Создан: {order['created_at']}\n"
        f"🚚 Доставка: {order['delivery_type']}\n"
        f"💵 Сумма: {order['total']}₽\n"
    )
    
    if order['delivery_type'] == 'Самовывоз' and order['status'] in ['Готов', 'В пути', 'Доставлен']:
        order_text += "\n🏪 Адрес самовывоза:\nг. Москва, ул. Велосипедная, 1\n⏰ 10:00-20:00"
    
    await callback.message.edit_text(order_text, reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard))

# ДЕМО-ФУНКЦИЯ ДЛЯ СИМУЛЯЦИИ ПРОГРЕССА
@router.callback_query(F.data.startswith("simulate_progress_"))
async def simulate_order_progress_demo(callback: CallbackQuery, bot: Bot):
    """Демо-функция для симуляции прогресса заказа"""
    order_id = callback.data.split('_')[2]
    
    if order_id in user_orders:
        await simulate_order_progress(bot, order_id)
        await check_order_status(callback, bot)  # Показываем обновленный статус
    else:
        await callback.answer("❌ Заказ не найден")