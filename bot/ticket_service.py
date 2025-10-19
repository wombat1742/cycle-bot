from sqlmodel import Session, select
from uuid import uuid4
from datetime import datetime
from models import Ticket, Message, Attachment, User, TicketStatus
from aiogram.types import User as TgUser
from utils import create_user_from_telegram
import logging

logger = logging.getLogger(__name__)

class TicketService:
    def __init__(self, session: Session):
        self.session = session
    
    async def create_ticket(self, tg_user: TgUser, initial_message: str, 
                          chat_id: str, msg_id: str) -> Ticket:
        """Создание нового тикета"""
        user = await self._get_or_create_user(tg_user)
        
        ticket = Ticket(
            id=uuid4(),
            user_id=user.id,
            status=TicketStatus.OPEN,
            opened_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        message = Message(
            id=uuid4(),
            text=initial_message,
            ticket_id=ticket.id,
            user_id=user.id,
            is_staff=False,
            chat_id=chat_id,
            msg_id=msg_id,
            created_at=datetime.now()
        )
        
        self.session.add(ticket)
        self.session.add(message)
        self.session.commit()
        self.session.refresh(ticket)
        
        logger.info(f"Создан новый тикет {ticket.id} для пользователя {user.id}")
        return ticket
    
    async def add_message_to_ticket(self, ticket_id: str, tg_user: TgUser, 
                                  text: str, chat_id: str, msg_id: str,
                                  is_staff: bool = False) -> Message:
        """Добавление сообщения в существующий тикет"""
        from uuid import UUID
        
        message = Message(
            id=uuid4(),
            text=text,
            ticket_id=UUID(ticket_id),
            user_id=tg_user.id,
            is_staff=is_staff,
            chat_id=chat_id,
            msg_id=msg_id,
            created_at=datetime.now()
        )
        
        ticket = self.session.get(Ticket, UUID(ticket_id))
        if ticket:
            ticket.updated_at = datetime.now()
        
        self.session.add(message)
        self.session.commit()
        self.session.refresh(message)
        
        logger.info(f"Добавлено сообщение в тикет {ticket_id}")
        return message
    
    async def add_message_with_attachments(self, ticket_id: str, tg_user: TgUser,
                                         text: str, chat_id: str, msg_id: str,
                                         file_ids: List[str]) -> Message:
        """Добавление сообщения с вложениями"""
        message = await self.add_message_to_ticket(
            ticket_id, tg_user, text, chat_id, msg_id
        )
        
        for file_id in file_ids:
            attachment = Attachment(
                file_id=file_id,
                message_id=message.id
            )
            self.session.add(attachment)
        
        self.session.commit()
        return message
    
    async def get_user_tickets(self, user_id: int, status: str = None) -> List[Ticket]:
        """Получение тикетов пользователя"""
        query = select(Ticket).where(Ticket.user_id == user_id)
        
        if status:
            query = query.where(Ticket.status == status)
        
        query = query.order_by(Ticket.updated_at.desc())
        return self.session.exec(query).all()
    
    async def get_ticket_messages(self, ticket_id: str) -> List[Message]:
        """Получение сообщений тикета"""
        from uuid import UUID
        query = select(Message).where(Message.ticket_id == UUID(ticket_id)).order_by(Message.created_at)
        return self.session.exec(query).all()
    
    async def get_open_ticket_by_user(self, user_id: int) -> Optional[Ticket]:
        """Получение открытого тикета пользователя"""
        query = select(Ticket).where(
            (Ticket.user_id == user_id) & 
            (Ticket.status == TicketStatus.OPEN)
        )
        return self.session.exec(query).first()
    
    async def close_ticket(self, ticket_id: str) -> Ticket:
        """Закрытие тикета"""
        from uuid import UUID
        ticket = self.session.get(Ticket, UUID(ticket_id))
        if ticket:
            ticket.status = TicketStatus.CLOSED
            ticket.updated_at = datetime.now()
            self.session.add(ticket)
            self.session.commit()
            self.session.refresh(ticket)
        
        return ticket
    
    async def _get_or_create_user(self, tg_user: TgUser) -> User:
        """Получение или создание пользователя"""
        user = self.session.get(User, tg_user.id)
        if not user:
            user = create_user_from_telegram(tg_user)
            self.session.add(user)
            self.session.commit()
            self.session.refresh(user)
        
        return user