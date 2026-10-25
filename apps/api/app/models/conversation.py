import uuid

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.models.enums import ConversationStatus, db_enum


class Conversation(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "conversations"

    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), index=True)
    status: Mapped[ConversationStatus] = mapped_column(
        db_enum(ConversationStatus, "conversationstatus"),
        default=ConversationStatus.OPEN,
    )

    # 刻意不绑定单个 order_id：一次客服会话可能涉及多个订单，
    # 后续如需关联，增加 conversation_orders 关联表。
