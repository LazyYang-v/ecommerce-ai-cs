from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.models.enums import ProductStatus


class ProductPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    description: str | None
    price: Decimal  # 金额序列化为字符串，避免浮点精度问题
    stock: int
    status: ProductStatus
    created_at: datetime


class ProductPage(BaseModel):
    items: list[ProductPublic]
    total: int
    page: int
    page_size: int
