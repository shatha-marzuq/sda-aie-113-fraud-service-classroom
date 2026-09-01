import logging
import sys

import structlog

SENSITIVE_KEYS = {"password", "token", "secret", "national_id", "card_number"}

log = structlog.get_logger("fraud_service")


def _mask_sensitive(logger, method, event_dict):
    for key in list(event_dict):
        if key.lower() in SENSITIVE_KEYS:
            event_dict[key] = "***MASKED***"
    return event_dict


def configure_logging(level: str = "INFO") -> None:
    logging.basicConfig(stream=sys.stdout, level=level)
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso", utc=True),
            _mask_sensitive,
            structlog.processors.JSONRenderer(),
        ]
    )