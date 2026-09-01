from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Gateway runtime configuration.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
    )

    app_name: str = "vpp-api-gateway"
    environment: str = "development"

    # 默认开启 mock，第一周开发不依赖其他服务
    mock_mode: bool = True

    http_timeout_seconds: float = 5.0

    # Downstream service addresses
    meter_service_url: str = "http://localhost:8001"
    ingestion_service_url: str = "http://localhost:8002"
    identity_service_url: str = "http://localhost:8003"
    fl_service_url: str = "http://localhost:8004"
    privacy_service_url: str = "http://localhost:8005"
    ledger_service_url: str = "http://localhost:8006"
    agent_service_url: str = "http://localhost:8007"


@lru_cache
def get_settings() -> Settings:
    return Settings()