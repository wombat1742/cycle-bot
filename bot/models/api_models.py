from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime

class AttachmentModel(BaseModel):
    id: Optional[int] = None
    file_id: str
    message_id: Optional[UUID] = None

class MessageModel(BaseModel):
    id: UUID
    text: str
    ticket_id: UUID
    user_id: int
    is_staff: bool
    chat_id: str
    msg_id: str
    created_at: datetime
    attachments: List[AttachmentModel] = []

class MessageWithAttachments(BaseModel):
    id: UUID
    text: str
    ticket_id: UUID
    user_id: int
    is_staff: bool
    chat_id: str
    msg_id: str
    created_at: datetime
    attachments: List[AttachmentModel] = []

class TicketModel(BaseModel):
    id: UUID
    user_id: int
    status: str
    opened_at: datetime
    updated_at: Optional[datetime] = None

class TicketWithMessages(TicketModel):
    messages: List[MessageModel] = []

# Request models
class CreateTicketRequest(BaseModel):
    id: UUID
    user_id: int
    status: str = "open"
    opened_at: datetime
    updated_at: Optional[datetime] = None

class CreateMessageRequest(BaseModel):
    id: UUID
    text: str
    ticket_id: UUID
    user_id: int
    is_staff: bool
    chat_id: str
    msg_id: str
    created_at: datetime
    attachments: List[AttachmentModel] = []