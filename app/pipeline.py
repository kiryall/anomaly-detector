from __future__ import annotations

import re
import shutil
from collections.abc import Callable
from pathlib import Path

from app.image_scanner import ImageScanner
from app.predictor import Predictor
from app.schemas.detection import DetectionResult
from app.services.logger import logger
from app.services.state import state
from app.config.paths import Paths


class Pipeline:
    """Основной pipeline обработки изображений."""

    def __init__(
        self,
        image_scanner: ImageScanner,
        paths: Paths,
    ) -> None:
        self._image_scanner = image_scanner
        self._paths = paths

    def run(
        self,
        input_folder: Path,
        model_path: Path,
        confidence_threshold: float,
        progress_callback: Callable[[int, int], None] | None = None,
    ) -> list[DetectionResult]:
        """Выполняет полный цикл обработки изображений."""
        if not input_folder.exists():
            raise FileNotFoundError(f"Папка не существует: {input_folder}")

        if not input_folder.is_dir():
            raise NotADirectoryError(f"Путь не является папкой: {input_folder}")

        if not model_path.exists():
            raise FileNotFoundError(f"Файл модели не найден: {model_path}")

        if not model_path.is_file():
            raise ValueError(f"Путь не является файлом: {model_path}")

        images = self._image_scanner.scan(input_folder)

        if not images:
            raise ValueError("В выбранной папке нет изображений.")

        state.statistics.reset()
        state.statistics.total_images = len(images)

        # Создаём Predictor внутри subprocess — YOLO модель не сериализуется
        predictor = Predictor()
        predictor.load_model(model_path)

        results: list[DetectionResult] = []

        for image_path in images:
            try:
                result = self._process_image(
                    predictor,
                    image_path,
                    confidence_threshold,
                )
                results.append(result)
            except (
                FileNotFoundError,
                ValueError,
                RuntimeError,
                PermissionError,
                OSError,
            ) as error:
                logger.error("Ошибка обработки %s: %s", image_path.name, error)
                state.statistics.errors += 1

            state.statistics.processed_images += 1

            if progress_callback is not None:
                progress_callback(
                    state.statistics.processed_images,
                    state.statistics.total_images,
                )

        state.statistics.anomaly_images = sum(
            1 for r in results
            if r.detection_count > 0 and r.max_confidence >= confidence_threshold
        )
        state.statistics.normal_images = sum(
            1 for r in results
            if r.detection_count == 0 or r.max_confidence < confidence_threshold
        )

        logger.info(
            "Pipeline завершён: всего=%d, аномалии=%d, норма=%d, ошибки=%d",
            len(results),
            state.statistics.anomaly_images,
            state.statistics.normal_images,
            state.statistics.errors,
        )

        return results

    def _process_image(
        self,
        predictor: Predictor,
        image_path: Path,
        confidence_threshold: float,
    ) -> DetectionResult:
        """Обрабатывает одно изображение: инференс + классификация + копирование."""
        result = predictor.predict(
            image_path=image_path,
            confidence=confidence_threshold,
        )

        if result.detection_count == 0 or result.max_confidence < confidence_threshold:
            class_name = "no_detection"
        else:
            best = max(result.detections, key=lambda d: d.confidence)
            class_name = best.class_name

        safe_name = self._safe_class_name(class_name)
        model_name = predictor.model_path.stem if predictor.model_path else "unknown"
        output_dir = self._paths.get_output_dir(model_name, safe_name)
        output_dir.mkdir(parents=True, exist_ok=True)

        destination = self._get_unique_destination(output_dir / image_path.name)
        shutil.copy2(image_path, destination)

        logger.info(
            "  %s → %s/",
            image_path.name,
            safe_name,
        )

        return result

    @staticmethod
    def _safe_class_name(class_name: str) -> str:
        """Возвращает безопасное имя для директории."""
        name = class_name.strip().lower()
        name = re.sub(r"[^\w\-]", "_", name)
        name = re.sub(r"_+", "_", name)
        name = name.lstrip("_").rstrip("_")
        if not name:
            name = "unknown"
        if ".." in name or name.startswith("/"):
            name = "unknown"
        return name

    @staticmethod
    def _get_unique_destination(destination: Path) -> Path:
        """Возвращает уникальный путь, если файл уже существует."""
        if not destination.exists():
            return destination

        stem = destination.stem
        suffix = destination.suffix
        counter = 1

        while True:
            new_name = f"{stem}_{counter}{suffix}"
            new_path = destination.parent / new_name

            if not new_path.exists():
                return new_path

            counter += 1
