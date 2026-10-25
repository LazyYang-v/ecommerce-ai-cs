"""业务枚举与 PG 原生 ENUM 列类型。"""
import enum

from sqlalchemy import Enum as SaEnum


class UserRole(enum.StrEnum):
    CUSTOMER = "customer"
    STAFF = "staff"
    ADMIN = "admin"


class ProductStatus(enum.StrEnum):
    ON_SALE = "on_sale"
    OFF_SALE = "off_sale"


class OrderStatus(enum.StrEnum):
    PENDING_PAYMENT = "pending_payment"
    PAID = "paid"
    SHIPPED = "shipped"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class ConversationStatus(enum.StrEnum):
    OPEN = "open"
    CLOSED = "closed"


class MessageSenderType(enum.StrEnum):
    USER = "user"
    AGENT = "agent"
    HUMAN_AGENT = "human_agent"
    SYSTEM = "system"


def db_enum(enum_cls: type[enum.Enum], name: str) -> SaEnum:
    """PostgreSQL 原生 ENUM 类型，取值为枚举成员的 value（小写下划线）。

    values_callable 必须显式传入：SQLAlchemy 默认按成员名（大写）存储。
    """
    return SaEnum(
        enum_cls,
        name=name,
        native_enum=True,
        values_callable=lambda cls: [m.value for m in cls],
    )
