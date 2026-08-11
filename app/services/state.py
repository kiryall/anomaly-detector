# app/services/state.py
# Состояние приложения и статистика обработки.

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass(slots=True)
class Statistics:
    """Статистика текущей обработки."""

    total_images: int = 0
    processed_images: int = 0

    anomaly_images: int = 0
    normal_images: int = 0

    errors: int = 0

    @property
    def progress(self) -> float:
        """Прогресс обработки (0..1)."""

        if self.total_images == 0:
            return 0.0

        return self.processed_images / self.total_images

    def reset(self) -> None:
        """Сброс статистики."""

        self.total_images = 0
        self.processed_images = 0
        self.anomaly_images = 0
        self.normal_images = 0
        self.errors = 0


@dataclass(slots=True)
class AppState:
    """Текущее состояние приложения."""

    # Что выбрал пользователь

    selected_model: str = ""

    selected_folder: Path | None = None

    images: list[Path] = field(default_factory=list)

    # Состояние обработки

    is_processing: bool = False

    status: str = "Готов"

    # Статистика

    statistics: Statistics = field(default_factory=Statistics)

    def reset(self) -> None:
        """Подготовить состояние к новой обработке."""

        self.selected_folder = None

        self.images.clear()

        self.is_processing = False
        self.status = "Готов"

        self.statistics.reset()


# Единственный экземпляр состояния приложения
state = AppState()