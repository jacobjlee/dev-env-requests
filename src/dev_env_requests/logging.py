import logging
import sys

import structlog

from src.dev_env_requests.config import settings


def setup_logging() -> None:
    """Configure structlog for structured logging.

    Behavior per environment:
        local:          Pretty colored output, DEBUG level.
        dev:            JSON output, DEBUG level.
        staging/prod:   JSON output, INFO level.

    Note:
        Call once at application startup before any logging occurs.
        Binds app, version, and environment to every log line globally.
        Quiets noisy libraries (uvicorn, sqlalchemy) to reduce log noise.
    """

    shared_processors: list[structlog.types.Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.CallsiteParameterAdder(
            [
                structlog.processors.CallsiteParameter.FILENAME,
                structlog.processors.CallsiteParameter.LINENO,
            ]
        ),
    ]

    renderer = (
        structlog.dev.ConsoleRenderer(colors=True)
        if settings.ENV == "local"
        else structlog.processors.JSONRenderer()
    )

    structlog.configure(
        processors=shared_processors
        + [
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    formatter = structlog.stdlib.ProcessorFormatter(
        processors=[
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            renderer,
        ],
        foreign_pre_chain=shared_processors,
    )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.addHandler(handler)
    root_logger.setLevel(
        logging.DEBUG if settings.ENV in {"local", "dev"} else logging.INFO
    )

    structlog.contextvars.bind_contextvars(
        app=settings.APP_NAME,
        version=settings.APP_VERSION,
        env=settings.ENV,
    )

    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(
        logging.INFO if settings.ENV in {"local", "dev"} else logging.WARNING
    )


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    """Return a named structured logger instance.

    Args:
        name: Logger name, typically __name__ of the calling module.

    Returns:
        structlog.stdlib.BoundLogger: A bound structured logger.

    Example:
        >>> logger = get_logger(__name__)
        >>> logger.info("app_started", port=8000)
    """
    return structlog.get_logger(name)
