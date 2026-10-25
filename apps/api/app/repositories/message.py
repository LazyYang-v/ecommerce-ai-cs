from collections.abc import Sequence
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Message


class MessageRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_page_by_conversation(
        self, *, conversation_id: UUID, page: int, page_size: int
    ) -> tuple[Sequence[Message], int]:
        condition = Message.conversation_id == conversation_id
        total = await self._session.scalar(
            select(func.count()).select_from(Message).where(condition)
        )
        stmt = (
            select(Message)
            .where(condition)
            .order_by(Message.created_at, Message.id)
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        items = (await self._session.execute(stmt)).scalars().all()
        return items, int(total or 0)

    def add(self, message: Message) -> Message:
        self._session.add(message)
        return message
