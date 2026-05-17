from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    service_name: str = "smartstock-service"
    service_port: int = 8000
    environment: str = "dev"
    log_level: str = "INFO"

    postgres_dsn: str = "postgresql+psycopg://smartstock:smartstock@postgres:5432/smartstock"
    clickhouse_url: str = "http://clickhouse:8123"
    redis_url: str = "redis://redis:6379/0"
    rabbitmq_url: str = "amqp://guest:guest@rabbitmq:5672/"

    minio_endpoint: str = "minio:9000"
    minio_access_key: str = "minioadmin"
    minio_secret_key: str = "minioadmin"
    minio_bucket: str = "smartstock"

    encryption_key: str = "wqQGuPy_J6xJ13W7PGQ9afixm9rlk7v5D7f8P5T5D5Q="
    default_language: str = "ru"

    mape_target_7d: float = 15.0
    recommendation_target_ms_10k_sku: int = 10_000

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
