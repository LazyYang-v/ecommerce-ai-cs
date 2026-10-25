from collections.abc import Sequence
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Conversation, Message
from app.repositories.conversation import ConversationRepository
from app.repositories.message import MessageRepository


class ConversationService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._conversations = ConversationRepository(session)
        self._messages = MessageRepository(session)

    async def create(self, *, user_id: UUID) -> Conversation:
        conversation = self._conversations.add(Conversation(user_id=user_id))
        await self._session.commit()
        await self._session.refresh(conversation)
        return conversation

    async def list_for_user(
        self, *, user_id: UUID, page: int, page_size: int
    ) -> tuple[Sequence[Conversation], int]:
        return await self._conversations.list_page_by_user(
            user_id=user_id, page=page, page_size=page_size
        )

    async def _get_owned(
        self, *, user_id: UUID, conversation_id: UUID
    ) -> Conversation | None:
        conversation = await self._conversations.get(conversation_id)
        if conversation is None or conversation.user_id != user_id:
            return None
        return conversation

    async def list_messages_for_user(
        self,
        *,
        user_id: UUID,
        conversation_id: UUID,
        page: int,
        page_size: int,
    ) -> tuple[Sequence[Message], int] | None:
        """归属校验：会话不存在或属于他人时返回 None（对外 404）。"""
        if await self._get_owned(
            user_id=user_id, conversation_id=conversation_id
        ) is None:
            return None
        return await self._messages.list_page_by_conversation(
            conversation_id=conversation_id, page=page, page_size=page_size
        )
