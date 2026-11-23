"""应用配置：从环境变量 / .env 读取。"""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """全局配置项。"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # 应用
    APP_NAME: str = "order-hub"
    APP_TITLE: str = "订单汇聚管理系统"
    APP_VERSION: str = "0.1.0"
    API_V1_PREFIX: str = "/api/v1"
    DEBUG: bool = True

    # 数据库
    DATABASE_URL: str = "postgresql+psycopg://order_hub:order_hub@127.0.0.1:5433/order_hub"
    DB_ECHO: bool = False

    # JWT
    JWT_SECRET: str = "order-hub-secret-change-me"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 720

    # 调度
    SCHEDULER_ENABLED: bool = True

    # 跨域
    CORS_ORIGINS: str = "http://localhost:5173,http://127.0.0.1:5173"

    # 时区与分页
    TIMEZONE: str = "Asia/Shanghai"
    DEFAULT_PAGE_SIZE: int = 10
    MAX_PAGE_SIZE: int = 100

    @property
    def cors_origins(self) -> list[str]:
        """把逗号分隔的跨域来源解析为列表。"""
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
