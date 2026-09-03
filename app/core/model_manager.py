# app/model_manager.py
# Модуль для управления ONNX-моделями.

from __future__ import annotations

import json
import threading
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from nicegui import run

from app.config.settings import settings
from app.services.logger import logger


@dataclass(slots=True, frozen=True)
class ModelInfo:
    """Неизменяемая информация о модели."""

    display_name: str   # best
    filename: str       # best.onnx
    path: Path


class ModelManager:
    """Класс для управления ONNX-моделями."""

    def __init__(self) -> None:
        self._models: list[ModelInfo] = []
        self._classes_cache: dict[str, list[str]] = {}
        self._lock = threading.Lock()
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
        """Возвращает список display_name доступных моделей."""
        return [model.display_name for model in self._models]

    # ---- Lifecycle ----

    def refresh(self) -> None:
        """Сканирует каталог моделей (синхронно, без загрузки модели)."""

        self._models.clear()
        self._classes_cache.clear()

        models_dir = settings.paths.models
        if not models_dir.exists():
            logger.warning("Каталог моделей не найден: %s", models_dir)
            return

        for file in sorted(models_dir.iterdir()):
            if file.is_file() and file.suffix.lower() == ".onnx":
                self._models.append(
                    ModelInfo(
                        display_name=file.stem,
                        filename=file.name,
                        path=file,
                    )
                )

    # ---- Lookup ----

    def exists(self, model_name: str) -> bool:
        """Проверяет, существует ли модель с указанным именем."""
        return self.get_model(model_name) is not None

    def get_model(self, model_name: str) -> ModelInfo | None:
        """Получить информацию о модели по display_name или filename."""
        for model in self._models:
            if model.filename == model_name or model.display_name == model_name:
                return model
        return None

    # ---- Class helpers ----

    def get_output_directories(self, model_name: str) -> list[Path]:
        """Возвращает список выходных директорий для классов модели."""
        classes = self.get_model_classes(model_name)
        if classes is None:
            return []
        model_info = self.get_model(model_name)
        folder_key = model_info.display_name if model_info else model_name
        return [settings.paths.get_output_dir(folder_key, cls) for cls in classes]

    # ---- Class loading (cached, thread-safe) ----

    def get_model_classes(self, model_name: str) -> list[str] | None:
        """Синхронно получает список классов модели (из кэша или с диска)."""
        cached: Optional[list[str]]

        with self._lock:
            cached = self._classes_cache.get(model_name)

        if cached is not None:
            return cached

        model_info = self.get_model(model_name)
        if model_info is None:
            return None

        classes = self._load_classes_blocking(model_info)

        if classes is not None:
            with self._lock:
                self._classes_cache[model_name] = classes

        return classes

    async def get_model_classes_async(self, model_name: str) -> list[str] | None:
        """Асинхронно получает классы модели — загружает через cpu_bound."""
        cached: Optional[list[str]]

        with self._lock:
            cached = self._classes_cache.get(model_name)

        if cached is not None:
            return cached

        model_info = self.get_model(model_name)
        if model_info is None:
            return None

        classes = await run.cpu_bound(
            lambda: self._load_classes_blocking(model_info)
        )

        if classes is not None:
            with self._lock:
                self._classes_cache[model_name] = classes

        return classes

    @staticmethod
    def _load_classes_blocking(model_info: ModelInfo) -> list[str] | None:
        """Внутренний метод — блокирующая загрузка классов ONNX."""
        try:
            # Пытаемся загрузить из ONNX metadata
            import onnxruntime as ort

            session = ort.InferenceSession(str(model_info.path))
            meta = session.get_modelmeta().custom_metadata_map
            names_raw = meta.get("names", "")

            if names_raw:
                loaded = eval(names_raw)  # noqa: S307
                if loaded and isinstance(loaded, dict):
                    # Keys могут быть int или str
                    classes = [loaded.get(i, loaded.get(str(i), "?")) for i in sorted(loaded.keys(), key=lambda x: int(x) if isinstance(x, str) else x)]
                    logger.info(
                        "Классы модели %s (из ONNX): %s",
                        model_info.filename,
                        classes,
                    )
                    return classes

            # Fallback: sidecar JSON
            names_json = model_info.path.with_suffix(".json")
            if names_json.exists():
                data = json.loads(names_json.read_text("utf-8"))
                names_dict = data.get("names", {})
                if names_dict:
                    classes = [
                        names_dict.get(str(i), names_dict.get(i, "?"))
                        for i in sorted(names_dict.keys(), key=lambda x: int(x) if isinstance(x, str) else x)
                    ]
                    logger.info(
                        "Классы модели %s (из JSON): %s",
                        model_info.filename,
                        classes,
                    )
                    return classes

        except Exception as e:
            logger.error(
                "Ошибка загрузки классов модели %s: %s",
                model_info.filename,
                e,
            )

        logger.warning(
            "Не удалось загрузить классы для модели %s",
            model_info.filename,
        )
        return None
