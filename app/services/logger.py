from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler

from app.config.settings import settings

logger = logging.getLogger("anomaly_detector")
logger.setLevel(logging.INFO)


def _setup_logger() -> None:
    """Создаёт RotatingFileHandler с безопасной инициализацией директории."""
    if logger.handlers:
        return

    log_dir = settings.paths.logs
    log_dir.mkdir(parents=True, exist_ok=True)

    handler = RotatingFileHandler(
        log_dir / "log",
        maxBytes=5 * 1024 * 1024,
        backupCount=3,
        encoding="utf-8",
    )
    handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
    logger.addHandler(handler)


# При первом импорте сразу настраиваем логгер (директория создаётся безопасно)
_setup_logger()
