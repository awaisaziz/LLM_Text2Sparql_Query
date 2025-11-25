"""Logging utilities for the Text-to-SPARQL backend."""
from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Optional


LOG_DIR = Path(__file__).resolve().parents[2] / "outputs" / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)
LOG_FILE = LOG_DIR / "backend.log"
DEFAULT_LEVEL = "INFO"

_logging_initialized = False

def get_logger(name: Optional[str] = None, level: str = DEFAULT_LEVEL) -> logging.Logger:
    global _logging_initialized

    logger = logging.getLogger(name)

    # Configure logging ONCE globally
    if not _logging_initialized:
        logger.setLevel(getattr(logging, level.upper(), logging.INFO))

        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )

        # Create file handler (overwrite mode)
        file_handler = logging.FileHandler(LOG_FILE, mode="w")
        file_handler.setFormatter(formatter)

        # Create console handler
        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(formatter)

        # Attach to ROOT LOGGER
        root_logger = logging.getLogger()
        root_logger.setLevel(logger.level)
        root_logger.addHandler(file_handler)
        root_logger.addHandler(stream_handler)

        _logging_initialized = True
        root_logger.info("Logging setup completed. Logs will be written to %s", LOG_FILE)

    return logger


