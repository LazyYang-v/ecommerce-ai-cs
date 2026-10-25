from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.models.enums import OrderStatus


class OrderSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    status: OrderStatus
    total_amount: Decimal
    created_at: datetime


class OrderItemPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    product_id: UUID
    product_name: str  # 下单时快照
    unit_price: Decimal  # 下单时快照
    quantity: int


class OrderDetail(BaseModel):
    id: UUID
    status: OrderStatus
    total_amount: Decimal
    created_at: datetime
    items: list[OrderItemPublic]


class OrderPage(BaseModel):
    items: list[OrderSummary]
    total: int
    page: int
    page_size: int
