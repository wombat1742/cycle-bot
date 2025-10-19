from sqlmodel import Session, select
from uuid import uuid4, UUID
from datetime import datetime
from typing import List, Optional, Dict, Any
from aiogram.types import User as TgUser, Message as TgMessage

from services.api_client import APIClient
from models.api_models import CreateTicketRequest, CreateMessageRequest, TicketWithMessages
from config import get_api_url
import logging

logger = logging.getLogger(__name__)

class TicketAPIService:
    def __init__(self, api_base_url: str = None):
        self.api_base_url = api_base_url or get_api_url()
    
    async def create_ticket(self, tg_user: TgUser, initial_message: str, 
                          chat_id: str, msg_id: str) -> Dict[str, Any]:
        """Создание нового тикета через API"""
        
        ticket_data = CreateTicketRequest(
            id=uuid4(),
            user_id=tg_user.id,
            status="open",
            opened_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        message_data = CreateMessageRequest(
            id=uuid4(),
            text=initial_message,
            ticket_id=ticket_data.id,
            user_id=tg_user.id,
            is_staff=False,
            chat_id=chat_id,
            msg_id=msg_id,
            created_at=datetime.now(),
            attachments=[]
        )
        
        async with APIClient(self.api_base_url) as api:
            try:
                # Создаем тикет
                ticket_result = await api.create_ticket(ticket_data.dict())
                logger.info(f"Создан тикет через API: {ticket_result}")
                
                # Добавляем первое сообщение
                message_result = await api.add_message_to_ticket(
                    str(ticket_data.id), message_data.dict()
                )
                
                return message_result  # Возвращает тикет с сообщениями
                
            except Exception as e:
                logger.error(f"Ошибка создания тикета через API: {e}")
                raise
    
    async def add_message_to_ticket(self, ticket_id: str, tg_user: TgUser, 
                                  text: str, chat_id: str, msg_id: str,
                                  is_staff: bool = False, 
                                  attachments: List[Dict] = None) -> Dict[str, Any]:
        """Добавление сообщения в тикет через API"""
        
        message_data = CreateMessageRequest(
            id=uuid4(),
            text=text,
            ticket_id=UUID(ticket_id),
            user_id=tg_user.id,
            is_staff=is_staff,
            chat_id=chat_id,
            msg_id=msg_id,
            created_at=datetime.now(),
            attachments=attachments or []
        )
        
        async with APIClient(self.api_base_url) as api:
            try:
                result = await api.add_message_to_ticket(ticket_id, message_data.dict())
                logger.info(f"Сообщение добавлено в тикет {ticket_id}")
                return result
            except Exception as e:
                logger.error(f"Ошибка добавления сообщения через API: {e}")
                raise
    
    async def get_ticket(self, ticket_id: str) -> Dict[str, Any]:
        """Получение тикета по ID через API"""
        async with APIClient(self.api_base_url) as api:
            try:
                return await api.get_ticket(ticket_id)
            except Exception as e:
                logger.error(f"Ошибка получения тикета {ticket_id}: {e}")
                raise
    
    async def get_user_tickets(self, user_id: int) -> List[Dict[str, Any]]:
        """Получение всех тикетов пользователя"""
        # Note: Этот эндпоинт нужно добавить в API
        # Пока эмулируем получение через фильтрацию
        return []  # Заглушка
    
    async def close_ticket(self, ticket_id: str) -> Dict[str, Any]:
        """Закрытие тикета через API"""
        # Note: Этот эндпоинт нужно добавить в API
        # Пока используем обновление статуса через добавление сообщения
        return {}  # Заглушка