from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables or .env file.

    Attributes:
        APP_NAME: Human-readable name of the application.
        APP_VERSION: Current version of the application.
        DEBUG: Enables debug mode and verbose logging when True.
        ENV: Deployment environment (local, dev, staging, prod).
        DATABASE_URL: SQLAlchemy-compatible async database connection string.
        API_PREFIX: URL prefix for all API routes.
        ALLOWED_ORIGINS: List of allowed CORS origins.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
    )

    # App
    APP_NAME: str = "Dev Environment Request System"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    ENV: str = "local"

    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./dev_env.db"

    # API
    API_PREFIX: str = "/api/v1"
    ALLOWED_ORIGINS: list[str] = ["*"]


@lru_cache
def get_settings() -> Settings:
    """Return a cached singleton instance of Settings.

    Returns:
        Settings: The application settings instance.

    Note:
        Cached via lru_cache so .env is only read once.
        Call get_settings.cache_clear() in tests to reset.
    """
    return Settings()


settings = get_settings()
