import logging

from advanced_alchemy.extensions.litestar import (
    AsyncSessionConfig,
    EngineConfig,
    SQLAlchemyAsyncConfig,
    SQLAlchemyPlugin,
)
from sqlalchemy import text

from src.dev_env_requests.config import settings

logger = logging.getLogger(__name__)


def _build_engine_config() -> EngineConfig:
    """Build engine config based on environment.

    Returns:
        EngineConfig: Engine configuration.

    Note:
        Pool settings are only applied for non-local environments
        since SQLite does not support connection pooling.
    """
    if settings.ENV != "local":
        return EngineConfig(pool_size=10, max_overflow=20)
    return EngineConfig()


session_config = AsyncSessionConfig(expire_on_commit=False)

alchemy_config = SQLAlchemyAsyncConfig(
    connection_string=settings.DATABASE_URL,
    before_send_handler="autocommit",
    session_config=session_config,
    create_all=settings.ENV == "local",
    engine_config=_build_engine_config(),
)

alchemy_plugin = SQLAlchemyPlugin(config=alchemy_config)


async def check_db_connection() -> bool:
    """Verify the database is reachable.

    Returns:
        bool: True if the database responds, False otherwise.

    Note:
        Used by the /ready readiness probe.
    """
    try:
        async with alchemy_config.get_engine().connect() as conn:
            await conn.execute(text("SELECT 1"))
        return True
    except Exception as e:
        logger.error("db_connection_check_failed", extra={"error": str(e)})
        return False
