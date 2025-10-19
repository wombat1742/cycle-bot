import logging
from aiogram import Bot, Dispatcher, Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.filters import Command, CommandObject
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from typing import Dict, List

from config import config
from api_ticket_service import APITicketService  # ✅ Правильный импорт

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Инициализация API сервиса ✅ ДОБАВЬ ЭТО
ticket_service = APITicketService(
    api_base_url=config.API_URL,
    api_token=config.API_TOKEN
)

# Роутер
router = Router()

# Остальной код без изменений...

# ID администраторов/поддержки из конфига
SUPPORT_IDS = config.ADMIN_IDS
ADMIN_CHAT_ID = config.HELP_CHAT_ID

# Состояния для FSM
class SupportStates(StatesGroup):
    awaiting_support_message = State()
    replying_to_user = State()

# Структура тестов
TESTS = [
    {
        "id": 1,
        "name": "bike_type_selection",
        "title": "🚴 Подбор идеального велосипеда",
        "questions": [
            {
                "id": 1,
                "text": "Для каких целей планируете использовать велосипед?",
                "answers": [
                    {"id": 1, "key": "city", "value": 1, "text": "🏙️ Городские поездки"},
                    {"id": 2, "key": "sport", "value": 2, "text": "🏁 Спорт и тренировки"},
                    {"id": 3, "key": "tourism", "value": 3, "text": "🗺️ Туризм и походы"},
                    {"id": 4, "key": "offroad", "value": 4, "text": "🏔️ Бездорожье и горы"}
                ]
            },
            {
                "id": 2,
                "text": "Какой у вас уровень подготовки?",
                "answers": [
                    {"id": 5, "key": "beginner", "value": 1, "text": "🟢 Начинающий"},
                    {"id": 6, "key": "intermediate", "value": 2, "text": "🟡 Продолжающий"},
                    {"id": 7, "key": "pro", "value": 3, "text": "🔴 Профессионал"}
                ]
            },
            {
                "id": 3,
                "text": "Какой бюджет рассматриваете?",
                "answers": [
                    {"id": 8, "key": "budget", "value": 1, "text": "💰 До 20,000₽"},
                    {"id": 9, "key": "medium", "value": 2, "text": "💵 20,000-50,000₽"},
                    {"id": 10, "key": "premium", "value": 3, "text": "💎 Свыше 50,000₽"}
                ]
            }
        ]
    }
]

# Хранилища данных
user_progress = {}
user_support_messages = {}

@router.message(Command("start"))
async def start(message: Message):
    """Главное меню"""
    keyboard = [
        [
            InlineKeyboardButton(text="🚴 Подбор велосипеда", callback_data="test_1"),
            InlineKeyboardButton(text="🛒 Каталог", callback_data="catalog")
        ],
        [
            InlineKeyboardButton(text="📞 Связаться с поддержкой", callback_data="support"),
            InlineKeyboardButton(text="ℹ️ О магазине", callback_data="about")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(inline_keyboard=keyboard)
    
    await message.answer(
        f"🚴‍♂️ Добро пожаловать в {config.SHOP_NAME}!\n\n"
        "Выберите опцию:",
        reply_markup=reply_markup
    )

@router.callback_query(F.data == "about")
async def handle_about(callback: CallbackQuery):
    """Информация о магазине"""
    about_text = (
        f"🏪 **{config.SHOP_NAME}**\n\n"
        f"📞 Телефон: {config.SHOP_PHONE}\n"
        f"📍 Адрес: {config.SHOP_ADDRESS}\n\n"
        "🕒 Время работы:\n"
        "Пн-Пт: 9:00-21:00\n"
        "Сб-Вс: 10:00-20:00"
    )
    
    keyboard = [
        [InlineKeyboardButton(text="📞 Поддержка", callback_data="support")],
        [InlineKeyboardButton(text="📋 Главное меню", callback_data="main_menu")]
    ]
    
    await callback.message.edit_text(
        about_text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
    )
    await callback.answer()

@router.callback_query(F.data == "support")
async def handle_support_request(callback: CallbackQuery, state: FSMContext):
    """Обработка запроса в поддержку"""
    keyboard = [
        [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_support")]
    ]
    reply_markup = InlineKeyboardMarkup(inline_keyboard=keyboard)
    
    await callback.message.edit_text(
        "📞 **Служба поддержки**\n\n"
        "Напишите ваш вопрос, и мы ответим в ближайшее время:\n\n"
        "💬 _Просто напишите сообщение..._",
        reply_markup=reply_markup
    )
    
    # Устанавливаем состояние ожидания сообщения для поддержки
    await state.set_state(SupportStates.awaiting_support_message)
    await callback.answer()

@router.message(SupportStates.awaiting_support_message)
async def forward_to_support(message: Message, state: FSMContext, bot: Bot):
    """Пересылка сообщения в поддержку (анонимно)"""
    user = message.from_user
    message_text = message.text
    
    # 🔥 ДОБАВЛЯЕМ ВЫЗОВ API СЕРВИСА - ЭТОГО НЕТ В ТВОЕМ КОДЕ!
    try:
        logger.info("🔄 СОХРАНЕНИЕ ТИКЕТА В API...")
        from api_ticket_service import ticket_service  # Импортируем сервис
        
        # Сохраняем тикет в API
        api_result = await ticket_service.create_ticket(
            tg_user=user,
            message_text=message_text,
            chat_id=str(message.chat.id),
            msg_id=str(message.message_id)
        )
        
        ticket_id = api_result.get("ticket_id", "unknown")
        logger.info(f"✅ Тикет сохранен в API: {ticket_id}")
        
    except Exception as e:
        logger.error(f"❌ Ошибка сохранения в API: {e}")
        # Продолжаем работу даже если API недоступно
        ticket_id = "not_saved"
    
    # ⚠️ ДАЛЬШЕ ТВОЙ СУЩЕСТВУЮЩИЙ КОД, НО ДОБАВЛЯЕМ ticket_id
    support_message = (
        f"🆕 Новое обращение в поддержку\n\n"
        f"💬 Сообщение: {message_text}\n"
        f"👤 ID пользователя: {user.id}\n"
        f"👤 Имя: {user.first_name or 'Не указано'}\n"
        f"🎫 ID тикета: {ticket_id}\n"  # 🔥 ДОБАВИЛИ ticket_id
        f"📅 Время: {message.date.strftime('%Y-%m-%d %H:%M')}"
    )
    
    reply_keyboard = [
        [InlineKeyboardButton(text="📝 Ответить", callback_data=f"reply_{user.id}")],
        [InlineKeyboardButton(text="✅ Решено", callback_data=f"resolve_{user.id}")]
    ]
    reply_markup = InlineKeyboardMarkup(inline_keyboard=reply_keyboard)
    
    try:
        sent_message = await bot.send_message(
            chat_id=config.SUPPORT_ID,
            text=support_message,
            reply_markup=reply_markup
        )
        
        # 🔥 ОБНОВЛЯЕМ СОХРАНЕНИЕ С ticket_id
        if user.id not in user_support_messages:
            user_support_messages[user.id] = []
        
        user_support_messages[user.id].append({
            'user_message_id': message.message_id,
            'support_message_id': sent_message.message_id,
            'SUPPORT_ID': config.SUPPORT_ID,
            'user_name': user.first_name,
            'ticket_id': ticket_id  # 🔥 СОХРАНЯЕМ ID ТИКЕТА
        })
            
    except Exception as e:
        logger.error(f"Ошибка отправки поддержке {config.SUPPORT_ID}: {e}")
    
    # Подтверждение пользователю
    keyboard = [
        [InlineKeyboardButton(text="📋 Главное меню", callback_data="main_menu")]
    ]
    
    await message.answer(
        "✅ Ваше сообщение отправлено в поддержку!\n"
        "Мы ответим вам в ближайшее время.\n\n"
        "🕐 Обычно отвечаем в течение 5-15 минут.",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
    )
    
    # Сбрасываем состояние
    await state.clear()

@router.callback_query(F.data.startswith("reply_"))
async def handle_support_reply(callback: CallbackQuery, state: FSMContext):
    """Обработка ответа от поддержки"""
    user_id = int(callback.data.split('_')[1])
    
    user_name = "пользователь"
    if user_id in user_support_messages and user_support_messages[user_id]:
        user_name = user_support_messages[user_id][0].get('user_name', 'пользователь')
    
    await callback.message.edit_text(
        f"💬 Ответ {user_name} (ID: {user_id}):\n\n"
        "Введите ваш ответ:"
    )
    
    # Сохраняем данные для ответа
    await state.set_state(SupportStates.replying_to_user)
    await state.update_data(user_id=user_id, support_message_id=callback.message.message_id)
    await callback.answer()

@router.callback_query(F.data.startswith("resolve_"))
async def handle_resolve_support(callback: CallbackQuery):
    """Пометить обращение как решенное"""
    user_id = int(callback.data.split('_')[1])
    
    await callback.message.edit_text(
        f"✅ Обращение {user_id} помечено как решенное"
    )
    await callback.answer()

@router.message(SupportStates.replying_to_user)
async def handle_support_message(message: Message, state: FSMContext, bot: Bot, config=config):
    """Обработка сообщения от поддержки пользователю"""
    data = await state.get_data()
    user_id = data.get('user_id')
    support_message_text = message.text
    
    try:
        # 🔥 ДОБАВЛЯЕМ СОХРАНЕНИЕ ОТВЕТА В API
        ticket_id = None
        if user_id in user_support_messages and user_support_messages[user_id]:
            ticket_id = user_support_messages[user_id][0].get('ticket_id')
        
        if ticket_id and ticket_id != "not_saved":
            logger.info(f"💾 Сохранение ответа поддержки в API для тикета {ticket_id}")
            from api_ticket_service import ticket_service
            
            await ticket_service.add_message(
                ticket_id=ticket_id,
                tg_user=message.from_user,  # поддержка
                message_text=support_message_text,
                chat_id=str(message.chat.id),
                msg_id=str(message.message_id),
                is_staff=True  # 🔥 Важно - сообщение от поддержки!
            )
            logger.info(f"✅ Ответ поддержки сохранен в API")
        
        # ДАЛЬШЕ ТВОЙ СУЩЕСТВУЮЩИЙ КОД...
        user_chat_id = user_support_messages.get(user_id, [{}])[0].get('SUPPORT_ID')
        if user_chat_id:
            await bot.send_message(
                chat_id=user_chat_id,
                text=f"💬 **Ответ от поддержки:**\n\n{support_message_text}\n\n"
                     f"_Для продолжения диалога просто ответьте на это сообщение_"
            )
            await message.answer("✅ Ответ отправлен пользователю!")
        else:
            await message.answer("❌ Не удалось найти чат пользователя")
        
    except Exception as e:
        logger.error(f"❌ Ошибка отправки: {e}")
        await message.answer(f"❌ Ошибка отправки: {e}")
    
    await state.clear()

@router.message(F.reply_to_message)
async def forward_user_reply_to_support(message: Message, bot: Bot):
    """Пересылка ответа пользователя обратно в поддержку"""
    user = message.from_user
    message_text = message.text
    
    # Проверяем, является ли это ответом на сообщение поддержки
    reply_text = message.reply_to_message.text
    if "Ответ от поддержки" in reply_text:
        
        # Форматируем для поддержки
        support_message = (
            f"🔄 Ответ от пользователя {user.first_name} (ID: {user.id})\n\n"
            f"💬 Сообщение: {message_text}\n"
            f"📅 Время: {message.date.strftime('%H:%M')}"
        )
        
        # Отправляем всем поддержкам
        for support_id in SUPPORT_IDS:
            try:
                keyboard = [
                    [InlineKeyboardButton(text="📝 Ответить", callback_data=f"reply_{user.id}")],
                    [InlineKeyboardButton(text="✅ Решено", callback_data=f"resolve_{user.id}")]
                ]
                
                await bot.send_message(
                    chat_id=support_id,
                    text=support_message,
                    reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
                )
            except Exception as e:
                logger.error(f"Ошибка отправки поддержке {support_id}: {e}")
        
        await message.answer("✅ Ваш ответ отправлен в поддержку!")

@router.callback_query(F.data == "cancel_support")
async def handle_cancel_support(callback: CallbackQuery, state: FSMContext):
    """Отмена запроса в поддержку"""
    await state.clear()
    await start(callback.message)
    await callback.answer()

@router.callback_query(F.data == "main_menu")
async def handle_main_menu(callback: CallbackQuery):
    """Возврат в главное меню"""
    await start(callback.message)
    await callback.answer()

# Обработчики тестов и каталога (упрощенная версия)
@router.callback_query(F.data.startswith("test_"))
async def handle_test_selection(callback: CallbackQuery):
    """Обработка выбора теста"""
    test_id = int(callback.data.split('_')[1])
    user_id = callback.from_user.id
    
    test = next((t for t in TESTS if t['id'] == test_id), None)
    if not test:
        await callback.message.edit_text("Тест не найден")
        return
    
    user_progress[user_id] = {
        'test_id': test_id,
        'current_question': 0,
        'answers': {},
        'test_data': test
    }
    
    await show_question(callback)
    await callback.answer()

async def show_question(callback: CallbackQuery):
    """Показ вопроса теста"""
    user_id = callback.from_user.id
    
    if user_id not in user_progress:
        await callback.message.edit_text("Сессия устарела")
        return
    
    progress = user_progress[user_id]
    test = progress['test_data']
    current_q_index = progress['current_question']
    
    if current_q_index >= len(test['questions']):
        await finish_test(callback)
        return
    
    question = test['questions'][current_q_index]
    
    keyboard = []
    for answer in question['answers']:
        keyboard.append([InlineKeyboardButton(text=answer['text'], callback_data=f"answer_{answer['id']}")])
    
    if current_q_index > 0:
        keyboard.append([InlineKeyboardButton(text="⬅️ Назад", callback_data="back")])
    
    keyboard.append([InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_test")])
    
    reply_markup = InlineKeyboardMarkup(inline_keyboard=keyboard)
    
    progress_text = f"📊 Вопрос {current_q_index + 1}/{len(test['questions'])}"
    
    await callback.message.edit_text(
        f"{progress_text}\n\n{question['text']}",
        reply_markup=reply_markup
    )

@router.callback_query(F.data.startswith("answer_"))
async def handle_answer(callback: CallbackQuery):
    """Обработка ответа на вопрос теста"""
    user_id = callback.from_user.id
    
    if callback.data == "back":
        progress = user_progress[user_id]
        if progress['current_question'] > 0:
            progress['current_question'] -= 1
        await show_question(callback)
        return
    
    if callback.data == "cancel_test":
        if user_id in user_progress:
            del user_progress[user_id]
        await callback.message.edit_text("Тест отменен")
        await start(callback.message)
        return
    
    answer_id = int(callback.data.split('_')[1])
    
    progress = user_progress[user_id]
    test = progress['test_data']
    current_question = test['questions'][progress['current_question']]
    
    selected_answer = next((a for a in current_question['answers'] if a['id'] == answer_id), None)
    if not selected_answer:
        await callback.message.edit_text("Ошибка: ответ не найден")
        return
    
    progress['answers'][current_question['id']] = selected_answer['id']
    progress['current_question'] += 1
    
    await show_question(callback)
    await callback.answer()

async def finish_test(callback: CallbackQuery):
    """Завершение теста"""
    user_id = callback.from_user.id
    
    if user_id not in user_progress:
        await callback.message.edit_text("Сессия устарела")
        return
    
    progress = user_progress[user_id]
    
    # Рекомендации на основе теста
    recommendations = "🚲 Рекомендуем:\n• Городской велосипед - 25,000₽\n• Горный велосипед - 35,000₽"
    
    keyboard = [
        [InlineKeyboardButton(text="🛒 Перейти к покупкам", callback_data="catalog")],
        [InlineKeyboardButton(text="📞 Консультация", callback_data="support")],
        [InlineKeyboardButton(text="📋 Главное меню", callback_data="main_menu")]
    ]
    
    await callback.message.edit_text(
        f"✅ Тест завершен!\n\n{recommendations}",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
    )
    
    del user_progress[user_id]

@router.callback_query(F.data == "catalog")
async def handle_catalog(callback: CallbackQuery):
    """Показ каталога"""
    keyboard = [
        [InlineKeyboardButton(text="📦 Складные", callback_data="cat_folding")],
        [InlineKeyboardButton(text="🏔️ Горные", callback_data="cat_mountain")],
        [InlineKeyboardButton(text="🚴 Гибридные", callback_data="cat_hybrid")],
        [InlineKeyboardButton(text="📞 Консультация", callback_data="support")],
        [InlineKeyboardButton(text="📋 Главное меню", callback_data="main_menu")]
    ]
    
    await callback.message.edit_text(
        "🛒 **Каталог велосипедов**\n\n"
        "Выберите категорию:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
    )
    await callback.answer()

async def main():
    """Запуск бота"""
    bot = Bot(token=config.BOT_TOKEN)
    dp = Dispatcher()
    dp.include_router(router)
    
    print(f"🤖 Бот {config.SHOP_NAME} запущен!")
    print(f"📞 Поддержка: {len(SUPPORT_IDS)} администраторов")
    print("🚴 Система продажи велосипедов активна")
    
    await dp.start_polling(bot)

if __name__ == '__main__':
    import asyncio
    asyncio.run(main())