from __future__ import annotations

from pathlib import Path

from app.core.detector import Detector
from app.schemas.detection import DetectionResult
from app.services.logger import logger


class Predictor:
    """Сервис высокого уровня: управление моделью и инференс."""

    def __init__(self) -> None:
        self._detector: Detector | None = None
        self._model_path: Path | None = None

    @property
    def is_loaded(self) -> bool:
        """Загружена ли модель."""
        return self._detector is not None

    @property
    def model_path(self) -> Path | None:
        """Путь к текущей загруженной модели."""
        return self._model_path

    def load_model(self, model_path: Path) -> None:
        """Загружает модель по указанному пути."""
        logger.info("Загрузка модели: %s", model_path.name)

        self._detector = Detector(model_path)
        self._model_path = model_path

        logger.info("Модель загружена: %s", model_path.name)

    def predict(
        self,
        image_path: Path,
        confidence: float = 0.25,
    ) -> DetectionResult:
        """Выполняет предсказание для изображения."""
        if self._detector is None:
            raise RuntimeError("Модель не загружена.")

        return self._detector.predict(
            image_path=image_path,
            confidence=confidence,
        )

    def unload_model(self) -> None:
        """Выгружает текущую модель."""
        logger.info("Выгрузка модели")

        self._detector = None
        self._model_path = None
