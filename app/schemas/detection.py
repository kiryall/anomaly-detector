from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(slots=True, frozen=True)
class BoundingBox:
    """Координаты bounding box."""

    x1: float
    y1: float
    x2: float
    y2: float


@dataclass(slots=True, frozen=True)
class Detection:
    """Одна найденная детекция."""

    class_id: int
    class_name: str
    confidence: float
    bbox: BoundingBox


@dataclass(slots=True, frozen=True)
class DetectionResult:
    """Результат обработки одного изображения."""

    image_path: Path
    has_anomaly: bool
    detections: tuple[Detection, ...]
    inference_time: float
    output_paths: tuple[Path, ...] = ()

    @property
    def detection_count(self) -> int:
        """Количество найденных объектов."""
        return len(self.detections)

    @property
    def max_confidence(self) -> float:
        """Максимальная уверенность среди всех детекций."""
        if not self.detections:
            return 0.0
        return max(d.confidence for d in self.detections)
