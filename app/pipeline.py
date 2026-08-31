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

                valid_count = sum(
                    1 for d in result.detections
                    if d.confidence >= confidence_threshold
                )
                if valid_count > 0:
                    state.statistics.anomaly_images += 1
                else:
                    state.statistics.normal_images += 1

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

        # Фильтруем детекции по порогу
        valid_detections = tuple(
            d for d in result.detections
            if d.confidence >= confidence_threshold
        )

        model_name = predictor.model_path.stem if predictor.model_path else "unknown"

        if not valid_detections:
            # Нет валидных детекций → no_defect (оригинал без изменений)
            safe_name = self._safe_class_name("no_defect")
            output_dir = self._paths.get_output_dir(model_name, safe_name)
            output_dir.mkdir(parents=True, exist_ok=True)

            destination = self._get_unique_destination(output_dir / image_path.name)
            shutil.copy2(image_path, destination)

            logger.info(
                "  %s → no_defect/",
                image_path.name,
            )

        else:
            # Отрисовываем все валидные детекции на одном изображении
            annotated_image = self._draw_detections(
                image_path,
                valid_detections,
            )

            # Получаем уникальные классы с сохранением порядка
            class_names = tuple(
                dict.fromkeys(
                    d.class_name for d in valid_detections
                )
            )

            for class_name in class_names:
                safe_name = self._safe_class_name(class_name)
                output_dir = self._paths.get_output_dir(model_name, safe_name)
                output_dir.mkdir(parents=True, exist_ok=True)

                destination = self._get_unique_destination(
                    output_dir / image_path.name
                )
                self._save_image(annotated_image, destination)

                logger.info(
                    "  %s → %s/",
                    image_path.name,
                    safe_name,
                )

        return result

    def _draw_detections(
        self,
        image_path: Path,
        detections: tuple,
    ) -> object:
        """Отрисовывает bounding boxes на изображении и возвращает PIL Image."""
        from PIL import Image, ImageDraw, ImageFont

        image = Image.open(image_path).convert("RGB")
        draw = ImageDraw.Draw(image)

        # Цвета для разных классов
        class_colors: dict[int, str] = {
            0: "red",
            1: "blue",
            2: "green",
            3: "yellow",
            4: "magenta",
            5: "orange",
            6: "cyan",
            7: "purple",
            8: "brown",
            9: "pink",
        }

        # Шрифт — увеличенный для читаемости
        font_size = 40
        font = self._load_font(font_size)

        for detection in detections:
            bbox = detection.bbox
            color = class_colors.get(detection.class_id, "red")

            draw.rectangle(
                [bbox.x1, bbox.y1, bbox.x2, bbox.y2],
                outline=color,
                width=5,
            )

            label = (
                f"{detection.class_name} "
                f"{detection.confidence:.2f}"
            )
            bbox_coords = draw.textbbox(
                (bbox.x1, bbox.y1 - font_size - 4),
                label,
                font=font,
            )
            draw.rectangle(bbox_coords, fill=color)
            draw.text(
                (bbox.x1, bbox.y1 - font_size - 4),
                label,
                fill="white",
                font=font,
            )

        return image

    @staticmethod
    def _load_font(size: int) -> object:
        """Загружает шрифт с поддержкой кириллицы."""
        from PIL import ImageFont

        # Пробуем системные шрифты с кириллицей
        font_paths = [
            "C:/Windows/Fonts/arial.ttf",
            "C:/Windows/Fonts/segoeui.ttf",
            "C:/Windows/Fonts/tahoma.ttf",
        ]

        for font_path in font_paths:
            try:
                return ImageFont.truetype(font_path, size)
            except (OSError, IOError):
                continue

        # Фоллбэк — встроенный шрифт
        return ImageFont.load_default()

    def _save_image(
        self,
        image: object,
        destination: Path,
    ) -> None:
        """Сохраняет PIL Image в указанный путь."""
        suffix = destination.suffix.lower()

        if suffix == ".jpg" or suffix == ".jpeg":
            image.save(
                str(destination),
                format="JPEG",
                quality=95,
            )
        elif suffix == ".png":
            image.save(
                str(destination),
                format="PNG",
            )
        else:
            image.save(str(destination))

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
