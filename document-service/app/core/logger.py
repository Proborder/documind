import structlog
from structlog.contextvars import merge_contextvars


def setup_logging():
    structlog.configure(
        processors=[
            merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.JSONRenderer()
        ],
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True
    )

setup_logging()
logger = structlog.get_logger()
