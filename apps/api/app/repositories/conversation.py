from collections.abc import Sequence
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Conversation


class ConversationRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self, conversation_id: UUID) -> Conversation | None:
        return await self._session.get(Conversation, conversation_id)

    async def list_page_by_user(
        self, *, user_id: UUID, page: int, page_size: int
    ) -> tuple[Sequence[Conversation], int]:
        condition = Conversation.user_id == user_id
        total = await self._session.scalar(
            select(func.count()).select_from(Conversation).where(condition)
        )
        stmt = (
            select(Conversation)
            .where(condition)
            .order_by(Conversation.created_at.desc(), Conversation.id)
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        items = (await self._session.execute(stmt)).scalars().all()
        return items, int(total or 0)

    def add(self, conversation: Conversation) -> Conversation:
        self._session.add(conversation)
        return conversation
