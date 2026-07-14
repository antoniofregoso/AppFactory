"""Configuración de logging estructurado de la aplicación."""

import logging
import sys
from datetime import datetime, timezone

from pythonjsonlogger import json

from app.core.config.settings import settings


class CustomJsonFormatter(json.JsonFormatter):
    def add_fields(self, log_record, record, message_dict):
        super().add_fields(log_record, record, message_dict)
        log_record["timestamp"] = datetime.now(timezone.utc).isoformat()
        log_record["level"] = record.levelname
        log_record["logger"] = record.name
        log_record["module"] = record.module


def configure_logging():
    numeric_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)
    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(numeric_level)
    console_handler.setFormatter(
        CustomJsonFormatter("%(timestamp)s %(level)s %(logger)s %(message)s")
    )

    root_logger.handlers.clear()
    root_logger.addHandler(console_handler)

    logging.getLogger("multipart").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)

    logging.getLogger("api").info(
        "Logging configured",
        extra={"log_level": settings.LOG_LEVEL, "environment": "development"},
    )


def get_logger(name: str):
    return logging.getLogger(name)
