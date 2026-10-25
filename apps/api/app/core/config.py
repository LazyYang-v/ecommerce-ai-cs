from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Business API 配置，全部来自环境变量。"""

    model_config = SettingsConfigDict(extra="ignore")

    # 数据层（Step 5/6 使用）
    database_url: str = "postgresql+asyncpg://ecommerce:ecommerce@127.0.0.1:55432/ecommerce"
    redis_url: str = "redis://127.0.0.1:56379/0"

    # 用户 JWT（Step 6 使用；为空时签发接口应 fail-closed）
    jwt_secret: str = ""
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60 * 24

    # Agent 通信（Step 3 使用）
    agent_url: str = "http://127.0.0.1:8001"
    internal_service_token: str = ""
    agent_timeout_seconds: float = 15.0


@lru_cache
def get_settings() -> Settings:
    return Settings()
