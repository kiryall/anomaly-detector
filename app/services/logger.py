from __future__ import annotations

import codecs
import logging
import sys
from logging.handlers import RotatingFileHandler

from app.config.settings import settings

# Fix Windows console encoding for Unicode (before any logging)
if sys.platform == "win32":
    sys.stdout = codecs.getwriter("utf-8")(sys.stdout.buffer, "strict")
    sys.stderr = codecs.getwriter("utf-8")(sys.stderr.buffer, "strict")

logger = logging.getLogger("anomaly_detector")
logger.setLevel(logging.INFO)


def _setup_logger() -> None:
    """Создаёт RotatingFileHandler + ConsoleHandler с безопасной инициализацией директории."""
    if logger.handlers:
        return

    log_dir = settings.paths.logs
    log_dir.mkdir(parents=True, exist_ok=True)

    # Console handler — основные логи и действия
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(
        logging.Formatter("[%(levelname)s] %(message)s")
    )
    logger.addHandler(console_handler)

    # File handler — полный лог
    file_handler = RotatingFileHandler(
        log_dir / "log",
        maxBytes=5 * 1024 * 1024,
        backupCount=3,
        encoding="utf-8",
    )
    file_handler.setFormatter(
        logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
    )
    logger.addHandler(file_handler)


# При первом импорте сразу настраиваем логгер (директория создаётся безопасно)
_setup_logger()
