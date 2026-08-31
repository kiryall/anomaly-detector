from __future__ import annotations

import time
from pathlib import Path

from app.schemas.detection import Detection, DetectionResult
from app.services.logger import logger


class Detector:
    """Низкоуровневый адаптер для YOLO-модели."""

    def __init__(self, model_path: Path) -> None:
        if not model_path.exists():
            raise FileNotFoundError(f"Файл модели не найден: {model_path}")

        if not model_path.is_file():
            raise ValueError(f"Путь не является файлом: {model_path}")

        logger.info("Загрузка модели: %s", model_path)

        from ultralytics import YOLO

        self._model = YOLO(model_path)

        logger.info("Модель загружена: %s", model_path)

    def predict(
        self,
        image_path: Path,
        confidence: float = 0.25,
    ) -> DetectionResult:
        """Выполняет инференс и возвращает DetectionResult."""
        if not image_path.exists():
            raise FileNotFoundError(f"Изображение не найдено: {image_path}")

        start_time = time.perf_counter()

        results = self._model.predict(
            source=str(image_path),
            conf=confidence,
            verbose=False,
        )

        inference_time = time.perf_counter() - start_time

        result = results[0]

        detections = self._parse_result(result)

        has_anomaly = len(detections) > 0

        logger.info(
            "Детекция %s: аномалия=%s, объектов=%d, время=%.3fs",
            image_path.name,
            has_anomaly,
            len(detections),
            inference_time,
        )

        return DetectionResult(
            image_path=image_path,
            has_anomaly=has_anomaly,
            detections=detections,
            inference_time=inference_time,
        )

    def _parse_result(
        self,
        result: object,
    ) -> tuple[Detection, ...]:
        """Преобразует сырой YOLO result в tuple[Detection, ...]."""
        from ultralytics.engine.results import Results

        if not isinstance(result, Results):
            return ()

        boxes = result.boxes

        if boxes is None or len(boxes) == 0:
            return ()

        detections: list[Detection] = []

        for i in range(len(boxes)):
            box = boxes[i]
            class_id = int(box.cls)
            confidence = float(box.conf)
            class_name = result.names.get(class_id, str(class_id))

            detections.append(
                Detection(
                    class_id=class_id,
                    class_name=class_name,
                    confidence=confidence,
                )
            )

        return tuple(detections)
