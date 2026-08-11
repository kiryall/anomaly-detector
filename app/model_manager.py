# app/model_manager.py
# Модуль для управления моделями.

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from app.config.models import SUPPURTED_EXTENSIONS
from app.config.settings import settings


@dataclass(slots=True, frozen=True)
class ModelInfo:
    """Информация о модели."""

    display_name: str   # best
    filename: str       # best.pt
    path: Path

class ModelManager:
    """Класс для управления моделями."""

    def __init__(self):
        self._models: list[ModelInfo] = []
        self._classes_cache: dict[str, list[str]] = {}
        self.refresh()

    @property
    def models(self) -> list[ModelInfo]:
        """Возвращает список доступных моделей."""
        return self._models

    @property
    def select_options(self) -> dict[str, str]:
        """Опции для ui.select: {filename: filename (with extension)}."""
        return {model.filename: model.filename for model in self._models}

    @property
    def names(self) -> list[str]:
        """Возвращает список имен доступных моделей."""
        return [model.display_name for model in self._models]

    def refresh(self) -> None:
        """Сканирует каталог моделей."""

        self._models.clear()
        self._classes_cache.clear()

        for file in sorted(settings.paths.models.iterdir()):
            if file.is_file() and file.suffix.lower() in SUPPURTED_EXTENSIONS:
                self._models.append(
                    ModelInfo(
                        display_name=file.stem,
                        filename=file.name,
                        path=file,
                    )
                )

        from app.services.logger import logger

        logger.info("Модели обнаружены: %d", len(self._models))

    def exists(self, model_name: str) -> bool:
        """Проверяет, существует ли модель с указанным именем."""
        return self.get_model(model_name) is not None

    def get_model(self, model_name: str) -> ModelInfo | None:
        """Получить информацию о модели по имени."""
        for model in self._models:
            if model.filename == model_name or model.display_name == model_name:
                return model
        return None
    
    def get_output_directories(self, model_name: str) -> list[Path]:
        """Возвращает список выходных директорий для классов модели."""
        classes = self.get_model_classes(model_name)
        if classes is None:
            return []
        model_info = self.get_model(model_name)
        folder_key = model_info.display_name if model_info else model_name
        return [settings.paths.get_output_dir(folder_key, cls) for cls in classes]

    def get_model_classes(self, model_name: str) -> list[str] | None:
        """Получить список классов модели по имени."""
        if model_name in self._classes_cache:
            return self._classes_cache[model_name]

        model_info = self.get_model(model_name)
        if model_info is None:
            return None

        try:
            from ultralytics import YOLO

            model = YOLO(model_info.path)
            if hasattr(model, "names"):
                classes = list(model.names.values())
                self._classes_cache[model_name] = classes
                from app.services.logger import logger

                logger.info("Классы модели %s загружены: %s", model_name, classes)
                return classes
        except ValueError as e:
            from app.services.logger import logger

            logger.error("Ошибка загрузки модели %s: %s", model_name, e)
            print(f"Ошибка при загрузке модели {model_name}: {e}")

        return None
