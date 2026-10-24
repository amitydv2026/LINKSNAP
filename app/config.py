"""Application settings loaded from environment / .env."""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Default to local SQLite so the app runs with zero setup.
    # Docker and production override DATABASE_URL to point at Postgres.
    database_url: str = "sqlite:///./linksnap.db"
    secret_key: str = "dev-secret-change-me-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    short_code_length: int = 7
    lru_cache_size: int = 10000


settings = Settings()
