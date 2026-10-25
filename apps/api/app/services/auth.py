from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.security import create_access_token, hash_password, verify_password
from app.models import User
from app.repositories.user import UserRepository


class EmailAlreadyExistsError(Exception):
    pass


class InvalidCredentialsError(Exception):
    pass


class AuthService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._users = UserRepository(session)

    async def register(
        self, *, email: str, password: str, nickname: str | None
    ) -> User:
        normalized = email.lower()
        if await self._users.get_by_email(normalized) is not None:
            raise EmailAlreadyExistsError(normalized)
        user = self._users.add(
            User(
                email=normalized,
                password_hash=hash_password(password),
                nickname=nickname,
            )
        )
        await self._session.commit()
        await self._session.refresh(user)
        return user

    async def login(self, *, email: str, password: str) -> tuple[User, str]:
        user = await self._users.get_by_email(email.lower())
        # 统一错误，不泄露"邮箱是否已注册"
        if user is None or not user.is_active or not verify_password(
            password, user.password_hash
        ):
            raise InvalidCredentialsError
        settings = get_settings()
        token = create_access_token(
            user_id=str(user.id),
            secret=settings.jwt_secret,
            expires_minutes=settings.jwt_expire_minutes,
            algorithm=settings.jwt_algorithm,
        )
        return user, token
