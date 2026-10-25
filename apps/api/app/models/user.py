from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.models.enums import UserRole, db_enum


class User(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(255), unique=True)
    # 只保存安全哈希（argon2），绝不保存明文
    password_hash: Mapped[str] = mapped_column(String(255))
    nickname: Mapped[str | None] = mapped_column(String(64))
    role: Mapped[UserRole] = mapped_column(
        db_enum(UserRole, "userrole"), default=UserRole.CUSTOMER
    )
    is_active: Mapped[bool] = mapped_column(default=True)
