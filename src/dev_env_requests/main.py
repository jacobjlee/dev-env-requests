from litestar import Litestar, Router
from litestar.config.compression import CompressionConfig
from litestar.config.cors import CORSConfig
from litestar.openapi import OpenAPIConfig
from litestar.openapi.plugins import ScalarRenderPlugin

from src.dev_env_requests.api.health import system_router
from src.dev_env_requests.api.requests import EnvironmentRequestController
from src.dev_env_requests.config import settings
from src.dev_env_requests.database import alchemy_plugin
from src.dev_env_requests.logging import get_logger, setup_logging

logger = get_logger(__name__)

cors_config = CORSConfig(
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
    allow_credentials=settings.ENV in {"staging", "prod"},
)

openapi_config = (
    OpenAPIConfig(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description="🖥️ Manage developer environment requests",
        render_plugins=[ScalarRenderPlugin()],
        path="/docs",
    )
    if settings.ENV != "prod"
    else None
)

api_router = Router(
    path=settings.API_PREFIX,
    route_handlers=[EnvironmentRequestController],
)


async def on_startup() -> None:
    """Run setup tasks on application startup.

    Note:
        Sets up logging first so all subsequent logs are structured.
        Table creation on local is handled by SQLAlchemyAsyncConfig(create_all=...).
        dev/staging/prod use Alembic migrations instead.
    """
    setup_logging()
    logger.info(
        "app_started",
        app=settings.APP_NAME,
        version=settings.APP_VERSION,
        env=settings.ENV,
        docs_enabled=settings.ENV != "prod",
    )


async def on_shutdown() -> None:
    """Run cleanup tasks on application shutdown."""
    logger.info("app_shutdown", app=settings.APP_NAME)


app = Litestar(
    route_handlers=[system_router, api_router],
    plugins=[alchemy_plugin],
    cors_config=cors_config,
    compression_config=CompressionConfig(backend="gzip"),
    openapi_config=openapi_config,
    on_startup=[on_startup],
    on_shutdown=[on_shutdown],
    debug=settings.DEBUG,
)
