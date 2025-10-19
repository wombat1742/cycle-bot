from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext

from states.support_states import SupportStates
from services.ticket_service import TicketService
from keyboards import get_support_keyboard, get_ticket_actions_keyboard
from utils import format_ticket_info
import logging

logger = logging.getLogger(__name__)

class SupportHandlers:
    def __init__(self, ticket_service: TicketService, support_chat_id: str = None):
        self.router = Router()
        self.ticket_service = ticket_service
        self.support_chat_id = support_chat_id
        
        self.router.message.register(self.start_support, Command("support"))
        self.router.message.register(self.handle_support_message, StateFilter(SupportStates.waiting_for_support_message))
        self.router.message.register(self.handle_user_reply, F.reply_to_message)
        self.router.callback_query.register(self.handle_ticket_actions, F.data.startswith(("reply_", "close_")))
    
    async def start_support(self, message: Message, state: FSMContext):
        """Начало диалога с поддержкой"""
        user = message.from_user
        
        open_ticket = await self.ticket_service.get_open_ticket_by_user(user.id)
        
        if open_ticket:
            await message.answer(
                "📞 У вас уже есть активный тикет поддержки.\n"
                "Просто напишите ваш вопрос, и мы ответим в ближайшее время:",
                reply_markup=get_support_keyboard()
            )
            await state.set_state(SupportStates.waiting_for_support_message)
            await state.update_data(ticket_id=str(open_ticket.id))
        else:
            await message.answer(
                "📞 **Служба поддержки**\n\n"
                "Опишите вашу проблему или вопрос, и мы ответим в ближайшее время:",
                reply_markup=get_support_keyboard(),
                parse_mode="Markdown"
            )
            await state.set_state(SupportStates.waiting_for_support_message)
    
    async def handle_support_message(self, message: Message, state: FSMContext):
        """Обработка сообщения для поддержки"""
        user = message.from_user
        text = message.text or message.caption or "📎 Сообщение с вложением"
        
        if text == "❌ Отмена":
            await message.answer("❌ Создание тикета отменено", reply_markup=get_main_menu_keyboard())
            await state.clear()
            return
        
        data = await state.get_data()
        ticket_id = data.get('ticket_id')
        
        try:
            if ticket_id:
                ticket_msg = await self.ticket_service.add_message_to_ticket(
                    ticket_id, user, text, 
                    str(message.chat.id), str(message.message_id)
                )
                await message.answer("✅ Сообщение добавлено в ваш тикет!")
            else:
                ticket = await self.ticket_service.create_ticket(
                    user, text, str(message.chat.id), str(message.message_id)
                )
                await state.update_data(ticket_id=str(ticket.id))
                await message.answer(
                    f"✅ Ваше обращение зарегистрировано!\n"
                    f"Номер тикета: `{ticket.id}`\n"
                    f"Мы ответим вам в ближайшее время.",
                    parse_mode="Markdown"
                )
            
            if self.support_chat_id:
                await self._forward_to_support(message, ticket_id or str(ticket.id))
                
        except Exception as e:
            logger.error(f"Ошибка создания тикета: {e}")
            await message.answer("❌ Произошла ошибка при создании тикета. Попробуйте позже.")
        
        await state.clear()
    
    async def handle_user_reply(self, message: Message):
        """Обработка ответа пользователя на сообщение поддержки"""
        if message.reply_to_message and "Ответ от поддержки" in message.reply_to_message.text:
            user = message.from_user
            text = message.text
            
            open_ticket = await self.ticket_service.get_open_ticket_by_user(user.id)
            
            if open_ticket:
                await self.ticket_service.add_message_to_ticket(
                    str(open_ticket.id), user, text,
                    str(message.chat.id), str(message.message_id)
                )
                await message.answer("✅ Ваш ответ отправлен в поддержку!")
    
    async def handle_ticket_actions(self, callback: CallbackQuery, state: FSMContext):
        """Обработка действий с тикетом"""
        data = callback.data
        ticket_id = data.split('_')[1]
        
        if data.startswith('close_'):
            ticket = await self.ticket_service.close_ticket(ticket_id)
            await callback.message.edit_text(f"✅ Тикет {ticket_id} закрыт")
        elif data.startswith('reply_'):
            await state.set_state(SupportStates.waiting_for_support_reply)
            await state.update_data(ticket_id=ticket_id)
            await callback.message.answer("Введите ваш ответ пользователю:")
        
        await callback.answer()
    
    async def _forward_to_support(self, message: Message, ticket_id: str):
        """Пересылка сообщения в чат поддержки"""
        # Реализация пересылки
        pass