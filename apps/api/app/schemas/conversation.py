from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.models.enums import ConversationStatus, MessageSenderType


class ConversationPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    status: ConversationStatus
    created_at: datetime


class ConversationPage(BaseModel):
    items: list[ConversationPublic]
    total: int
    page: int
    page_size: int


class MessagePublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    sender_type: MessageSenderType
    content: str
    created_at: datetime


class MessagePage(BaseModel):
    items: list[MessagePublic]
    total: int
    page: int
    page_size: int
