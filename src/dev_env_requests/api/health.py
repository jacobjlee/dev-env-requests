from litestar import MediaType, Router, get
from litestar.response import Response
from litestar.status_codes import HTTP_200_OK, HTTP_503_SERVICE_UNAVAILABLE

from src.dev_env_requests.config import settings
from src.dev_env_requests.database import check_db_connection
from src.dev_env_requests.logging import get_logger

logger = get_logger(__name__)


@get("/health", tags=["System"], summary="Liveness probe")
async def health_check() -> dict:
    """K8s liveness probe — is the process alive?

    Returns:
        dict: App status, name, version, and environment.

    Note:
        No DB check here. Failure causes K8s to restart the pod.
    """
    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "env": settings.ENV,
    }


@get("/ready", tags=["System"], summary="Readiness probe")
async def readiness_check() -> Response:
    """K8s readiness probe — is the app ready to receive traffic?

    Returns:
        Response: 200 if ready, 503 if database is unreachable.

    Note:
        Checks DB connectivity. Failure removes pod from load balancer
        without restarting it.
    """
    db_ok = await check_db_connection()
    payload = {
        "status": "ready" if db_ok else "not ready",
        "checks": {
            "database": "ok" if db_ok else "unreachable",
        },
    }

    if not db_ok:
        logger.warning("readiness_check_failed", database="unreachable")
        return Response(
            content=payload,
            status_code=HTTP_503_SERVICE_UNAVAILABLE,
            media_type=MediaType.JSON,
        )

    return Response(
        content=payload,
        status_code=HTTP_200_OK,
        media_type=MediaType.JSON,
    )


@get("/", tags=["System"], summary="Root")
async def root() -> dict:
    """Root endpoint.

    Returns:
        dict: Welcome message and links to key endpoints.
    """
    return {
        "message": f"Welcome to {settings.APP_NAME}",
        "version": settings.APP_VERSION,
        "docs": "/docs" if settings.ENV != "prod" else "disabled",
        "health": "/health",
        "ready": "/ready",
    }


system_router = Router(
    path="/",
    route_handlers=[root, health_check, readiness_check],
    tags=["System"],
)
