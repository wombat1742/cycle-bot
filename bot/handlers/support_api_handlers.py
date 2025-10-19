from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from services.ticket_api_service import TicketAPIService
from states.support_states import SupportStates
from keyboards import get_support_keyboard, get_main_menu_keyboard
from config import get_api_url
import logging

logger = logging.getLogger(__name__)

class SupportAPIHandlers:
    def __init__(self, api_base_url: str = None):
        self.router = Router()
        self.ticket_service = TicketAPIService(api_base_url)
        
        self.router.message.register(self.start_support, Command("support"))
        self.router.message.register(self.handle_support_message, StateFilter(SupportStates.waiting_for_support_message))
        self.router.message.register(self.handle_user_reply, F.reply_to_message)
        self.router.message.register(self.handle_support_attachment, F.content_type.in_({'photo', 'document'}))
    
    async def start_support(self, message: Message, state: FSMContext):
        """Начало диалога с поддержкой через API"""
        user = message.from_user
        
        await message.answer(
            "📞 **Служба поддержки**\n\n"
            "Опишите вашу проблему или вопрос, и мы ответим в ближайшее время:",
            reply_markup=get_support_keyboard(),
            parse_mode="Markdown"
        )
        await state.set_state(SupportStates.waiting_for_support_message)
    
    async def handle_support_message(self, message: Message, state: FSMContext):
        """Обработка сообщения для поддержки через API"""
        user = message.from_user
        text = message.text or message.caption or "📎 Сообщение с вложением"
        
        if text == "❌ Отмена":
            await message.answer("❌ Создание тикета отменено", reply_markup=get_main_menu_keyboard())
            await state.clear()
            return
        
        try:
            # Создаем тикет через API
            ticket_result = await self.ticket_service.create_ticket(
                user, text, str(message.chat.id), str(message.message_id)
            )
            
            ticket_id = ticket_result.get('id')
            await message.answer(
                f"✅ Ваше обращение зарегистрировано!\n"
                f"Номер тикета: `{ticket_id}`\n"
                f"Мы ответим вам в ближайшее время.",
                parse_mode="Markdown",
                reply_markup=get_main_menu_keyboard()
            )
            
            logger.info(f"Создан тикет через API: {ticket_id}")
                
        except Exception as e:
            logger.error(f"Ошибка создания тикета через API: {e}")
            await message.answer(
                "❌ Произошла ошибка при создании тикета. Попробуйте позже.",
                reply_markup=get_main_menu_keyboard()
            )
        
        await state.clear()
    
    async def handle_user_reply(self, message: Message):
        """Обработка ответа пользователя на сообщение поддержки через API"""
        if message.reply_to_message and "Ответ от поддержки" in message.reply_to_message.text:
            user = message.from_user
            text = message.text
            
            # Здесь нужно получить ticket_id из контекста
            # В реальном приложении нужно хранить связь сообщений с тикетами
            ticket_id = await self._get_ticket_id_from_reply(message.reply_to_message)
            
            if ticket_id:
                try:
                    await self.ticket_service.add_message_to_ticket(
                        ticket_id, user, text,
                        str(message.chat.id), str(message.message_id)
                    )
                    await message.answer("✅ Ваш ответ отправлен в поддержку!")
                except Exception as e:
                    logger.error(f"Ошибка отправки ответа через API: {e}")
                    await message.answer("❌ Ошибка отправки ответа")
    
    async def handle_support_attachment(self, message: Message, state: FSMContext):
        """Обработка вложений для поддержки через API"""
        user = message.from_user
        file_id = None
        attachments = []
        
        if message.photo:
            file_id = message.photo[-1].file_id
        elif message.document:
            file_id = message.document.file_id
        
        if file_id:
            attachments = [{"file_id": file_id}]
            text = message.caption or "📎 Файл"
            
            try:
                ticket_result = await self.ticket_service.create_ticket(
                    user, text, str(message.chat.id), str(message.message_id)
                )
                
                await message.answer(
                    f"✅ Тикет с вложением создан!\n"
                    f"Номер: `{ticket_result.get('id')}`",
                    parse_mode="Markdown",
                    reply_markup=get_main_menu_keyboard()
                )
                
            except Exception as e:
                logger.error(f"Ошибка создания тикета с вложением: {e}")
                await message.answer("❌ Ошибка при обработке файла.")
    
    async def _get_ticket_id_from_reply(self, reply_message) -> Optional[str]:
        """Получение ID тикета из reply сообщения"""
        # В реальном приложении нужно хранить эту информацию
        # Например, в тексте сообщения или в отдельном хранилище
        return None  # Заглушка