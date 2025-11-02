import logging
import sys
from typing import List

import structlog
from structlog.typing import Processor

from puzzle_solver.config.settings import settings
from puzzle_solver.core.observability import correlation_id


def setup_logging():
    """Configure structlog and Python logging."""
    log_level = _get_log_level()

    _configure_standard_logging(log_level)
    _configure_structlog(log_level)

    logger = structlog.get_logger()
    logger.info("Logger configured", level=settings.LOG_LEVEL, format=settings.LOG_FORMAT, file=settings.LOG_FILE_PATH)
    return logger


def _get_log_level() -> int:
    """Get a numeric log level from settings."""
    return getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)


def _configure_standard_logging(log_level: int) -> None:
    """Configure Python standard logging."""
    handlers = _create_log_handlers()
    logging.basicConfig(
        format="%(message)s",
        level=log_level,
        handlers=handlers,
    )


def _create_log_handlers() -> List[logging.Handler]:
    """Create logging handlers based on configuration."""
    handlers = [logging.StreamHandler(sys.stdout)]

    if settings.LOG_FILE_PATH:
        handlers.append(logging.FileHandler(settings.LOG_FILE_PATH))

    return handlers


def _configure_structlog(log_level: int) -> None:
    """Configure structlog processors and settings."""
    processors = _create_processors()

    structlog.configure(
        processors=processors,
        wrapper_class=structlog.make_filtering_bound_logger(log_level),
        context_class=dict if settings.LOG_CONTEXT_CLASS == "dict" else None,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )


def _create_processors() -> List[Processor]:
    """Create structlog processors based on configuration."""
    processors: List[Processor] = [
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt=settings.LOG_TIMESTAMP_FORMAT),
        _add_correlation_id,
    ]

    if settings.LOG_INCLUDE_STACK_INFO:
        processors.append(structlog.processors.StackInfoRenderer())

    processors.append(structlog.processors.format_exc_info)
    processors.append(_create_renderer())

    return processors


def _add_correlation_id(logger, method_name, event_dict):
    """Add correlation ID to log events."""
    event_dict["correlation_id"] = correlation_id.get("")
    return event_dict


def _create_renderer() -> Processor:
    """Create appropriate log renderer based on format setting."""
    if settings.LOG_FORMAT.lower() == "json":
        return structlog.processors.JSONRenderer()
    return structlog.dev.ConsoleRenderer(colors=settings.LOG_COLORIZE)
