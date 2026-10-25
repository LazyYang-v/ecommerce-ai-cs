"""导入全部模型，Alembic autogenerate 依赖此处的完整注册。"""
from app.models.base import Base
from app.models.conversation import Conversation
from app.models.message import Message
from app.models.order import Order
from app.models.order_item import OrderItem
from app.models.product import Product
from app.models.user import User

__all__ = [
    "Base",
    "Conversation",
    "Message",
    "Order",
    "OrderItem",
    "Product",
    "User",
]
