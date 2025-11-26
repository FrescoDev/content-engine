"""
Structured logging configuration for Cloud Logging compatibility.
"""

import json
import logging
import sys
from datetime import datetime, timezone
from typing import Any


class CloudLoggingFormatter(logging.Formatter):
    """Formatter for structured JSON logs compatible with Cloud Logging."""

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        log_data: dict[str, Any] = {
            "severity": self._get_severity(record.levelno),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "message": record.getMessage(),
            "logger": record.name,
        }

        # Add extra fields (using getattr to avoid type errors)
        job_type = getattr(record, "job_type", None)
        if job_type:
            log_data["job_type"] = job_type
        run_id = getattr(record, "run_id", None)
        if run_id:
            log_data["run_id"] = run_id

        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_data)

    @staticmethod
    def _get_severity(levelno: int) -> str:
        """Map Python log levels to Cloud Logging severity."""
        mapping = {
            logging.DEBUG: "DEBUG",
            logging.INFO: "INFO",
            logging.WARNING: "WARNING",
            logging.ERROR: "ERROR",
            logging.CRITICAL: "CRITICAL",
        }
        return mapping.get(levelno, "INFO")


def get_logger(name: str) -> logging.Logger:
    """Get a configured logger instance."""
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    # Remove existing handlers
    logger.handlers.clear()

    # Add console handler with JSON formatter
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(CloudLoggingFormatter())
    logger.addHandler(handler)

    return logger
