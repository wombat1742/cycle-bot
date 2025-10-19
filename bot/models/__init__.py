from sqlmodel import SQLModel, Field, Relationship
from typing import List, Optional
from uuid import UUID, uuid4
from datetime import datetime
from decimal import Decimal

class TicketStatus:
    OPEN = "open"
    CLOSED = "closed"
    PENDING = "pending"

class User(SQLModel, table=True):
    id: int = Field(primary_key=True)
    first_name: str
    last_name: str
    username: Optional[str]
    
    tickets: List["Ticket"] = Relationship(back_populates="user")
    orders: List["Order"] = Relationship()

class TicketBase(SQLModel):
    id: UUID = Field(primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    status: str = Field(default=TicketStatus.OPEN)
    opened_at: datetime = Field(default=datetime.now())
    updated_at: Optional[datetime] = Field(default=None)

class Ticket(TicketBase, table=True):
    user: User = Relationship(back_populates="tickets")
    messages: List["Message"] = Relationship(back_populates="ticket")

class MessageBase(SQLModel):
    id: UUID = Field(primary_key=True)
    text: str
    ticket_id: UUID = Field(foreign_key="ticket.id")
    user_id: int
    is_staff: bool
    chat_id: str
    msg_id: str
    created_at: datetime = Field(default=datetime.now())

class Message(MessageBase, table=True):
    ticket: Ticket = Relationship(back_populates="messages")
    attachments: List["Attachment"] = Relationship(back_populates="message")

class AttachmentBase(SQLModel):
    file_id: str
    message_id: Optional[UUID] = Field(default=None, foreign_key="message.id")

class Attachment(AttachmentBase, table=True):
    __tablename__ = "attachments"
    id: Optional[int] = Field(default=None, primary_key=True)
    message: Optional[Message] = Relationship(back_populates="attachments")

# Дополнительные модели для магазина
class ProductType(SQLModel, table=True):
    __tablename__ = "product_types"
    id: int = Field(primary_key=True)
    name: str

class ProductBase(SQLModel):
    id: UUID = Field(primary_key=True)
    name: str
    description: str
    price: Decimal
    in_stock: int
    type_id: int = Field(foreign_key="product_types.id")
    photo_path: Optional[str]
    parent_product_id: Optional[UUID] = Field(foreign_key="product.id", default=None, nullable=True)

class Product(ProductBase, table=True):
    type: ProductType = Relationship()

class OrderBase(SQLModel):
    id: UUID = Field(primary_key=True, default=uuid4)
    user_id: int = Field(foreign_key="user.id")
    status: str
    payment_id: Optional[str] = None
    description: Optional[str] = None
    created_at: datetime = Field(default=datetime.now())
    updated_at: datetime = Field(default=datetime.now())

class Order(OrderBase, table=True):
    user: User = Relationship(back_populates="orders")

class ProductsInCart(SQLModel, table=True):
    __tablename__ = "product_in_cart"
    user_id: int = Field(foreign_key="user.id", primary_key=True)
    product_id: UUID = Field(foreign_key="product.id", primary_key=True)
    amount: int

class ProductInOrder(SQLModel, table=True):
    __tablename__ = "product_in_order"
    order_id: UUID = Field(foreign_key="order.id", primary_key=True)
    product_id: UUID = Field(foreign_key="product.id", primary_key=True)
    amount: int