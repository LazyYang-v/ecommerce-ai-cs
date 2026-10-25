from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Agent 服务配置，全部来自环境变量。"""

    model_config = SettingsConfigDict(extra="ignore")

    # 内部服务令牌；为空时 /internal/chat 一律拒绝（fail-closed）
    internal_service_token: str = ""
    # 预留给 Phase 2：Agent 经 Business API 受控接口调用业务工具
    business_api_url: str = "http://127.0.0.1:8000"


@lru_cache
def get_settings() -> Settings:
    return Settings()
