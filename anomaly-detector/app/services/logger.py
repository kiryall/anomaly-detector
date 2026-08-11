import logging
from logging.handlers import RotatingFileHandler

from app.config.settings import settings

LOG_FILE = settings.paths.logs / "log"

logger = logging.getLogger("anomaly_detector")
logger.setLevel(logging.INFO)

if not logger.handlers:
    settings.paths.logs.mkdir(parents=True, exist_ok=True)

    handler = RotatingFileHandler(
        LOG_FILE,
        maxBytes=5 * 1024 * 1024,
        backupCount=3,
        encoding="utf-8",
    )
    handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
    logger.addHandler(handler)
