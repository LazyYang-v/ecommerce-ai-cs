import uuid
from decimal import Decimal

from sqlalchemy import ForeignKey, Index, Numeric
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.models.enums import OrderStatus, db_enum


class Order(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "orders"
    __table_args__ = (Index("ix_orders_user_id_created_at", "user_id", "created_at"),)

    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))
    status: Mapped[OrderStatus] = mapped_column(
        db_enum(OrderStatus, "orderstatus"), default=OrderStatus.PENDING_PAYMENT
    )
    total_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2))
