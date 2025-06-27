import json
from typing import Any, Dict
from logging.config import dictConfig
from logging import (
    getLogger,
    Formatter,
    LogRecord
)

from src.core.config import settings


class JsonFormatter(Formatter):
    """
    Custom formatter to output logs in JSON format.
    Ensures that logs are machine-readable
    for monitoring systems.
    """

    def format(self, record: LogRecord) -> str:
        log_record = {
            "timestamp": self.formatTime(
                record,
                self.datefmt
            ),
            "level": record.levelname,
            "name": record.name,
            "message": record.getMessage(),
            "lineno": record.lineno,
            "pathname": record.pathname,
        }

        # Include exception info if available
        if record.exc_info:
            log_record[
                "exc_info"
            ] = self.formatException(
                record.exc_info
            )

        if record.exc_text:
            log_record["exc_text"] = record.exc_text

        # Add any extra fields passed to the logger
        if hasattr(record, "extra_info"):
            log_record.update(record.extra_info)

        return json.dumps(log_record)


def setup_logging():
    """
    Sets up the application's logging
    configuration using dictConfig.
    Logs will be output in JSON
    format to the console.
    """

    log_level = settings.LOG_LEVEL.upper()

    logging_config: Dict[str, Any] = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "json": {
                "()": "src.core.logging_config.JsonFormatter",
                "format": "{asctime} {levelname} {name} {message}",
            },
            "simple": {
                "format": "{asctime} - {levelname} - {name} - {message}",
            },
        },
        "handlers": {
            "console_json": {
                "class": "logging.StreamHandler",
                "formatter": "json",
                "level": log_level,
                "stream": "ext://sys.stdout",
            },
            "console_simple": {
                "class": "logging.StreamHandler",
                "formatter": "simple",
                "level": log_level,
                "stream": "ext://sys.stdout",
            },
        },
        "loggers": {

            # Root logger
            "": {
                "handlers": [
                    "console_simple" if settings.DEBUG_MODE else "console_json"
                ],
                "level": log_level,
                "propagate": True,
            },

            # Specific loggers for libraries can be configured here
            "uvicorn": {
                "handlers": [
                    "console_simple" if settings.DEBUG_MODE else "console_json"
                ],
                "level": "INFO",
                "propagate": False,
            },

            "uvicorn.error": {
                "handlers": [
                    "console_simple" if settings.DEBUG_MODE else "console_json"
                ],
                "level": "INFO",
                "propagate": False,
            },
            "uvicorn.access": {
                "handlers": [
                    "console_simple" if settings.DEBUG_MODE else "console_json"
                ],
                "level": "INFO",
                "propagate": False,
            },
            "sqlalchemy.engine": {
                "handlers": ["console_simple"],
                # Set to INFO to see
                # SQL queries if
                # DATABASE_ECHO is False
                "level": "WARNING",
                "propagate": False,
            }
        },
    }

    dictConfig(logging_config)

    getLogger(__name__).info(
        "Logging configured successfully."
    )
