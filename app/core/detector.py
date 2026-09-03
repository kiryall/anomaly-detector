from __future__ import annotations

import time
from pathlib import Path

import cv2
import numpy as np

from app.schemas.detection import BoundingBox, Detection, DetectionResult
from app.services.logger import logger


class Detector:
    """Низкоуровневый адаптер для ONNX-модели YOLO."""

    def __init__(self, model_path: Path) -> None:
        if not model_path.exists():
            raise FileNotFoundError(f"Файл модели не найден: {model_path}")

        if not model_path.is_file():
            raise ValueError(f"Путь не является файлом: {model_path}")

        logger.info("Загрузка ONNX-модели: %s", model_path)

        import onnxruntime as ort

        self._session = ort.InferenceSession(
            str(model_path),
            providers=["CPUExecutionProvider"],
        )

        # Метаданные модели
        self._input_name = self._session.get_inputs()[0].name
        self._output_names = [o.name for o in self._session.get_outputs()]
        self._input_shape = self._session.get_inputs()[0].shape  # [1, 3, H, W]
        self._imgsz = self._input_shape[2]  # квадратный ввод

        # Извлекаем классы из ONNX metadata или sidecar JSON
        self._classes: dict[int, str] = self._load_classes(model_path)

        logger.info("Модель загружена: %s (%d классов)", model_path, len(self._classes))

    @staticmethod
    def _load_classes(model_path: Path) -> dict[int, str]:
        """Загружает имена классов из ONNX metadata или sidecar JSON."""
        import json

        import onnxruntime as ort

        session = ort.InferenceSession(str(model_path))
        meta = session.get_modelmeta().custom_metadata_map
        names_raw = meta.get("names", "")

        if names_raw:
            try:
                loaded = eval(names_raw)  # noqa: S307
                if loaded and isinstance(loaded, dict):
                    return {int(k): v for k, v in loaded.items()}
            except Exception:
                pass

        # Fallback: sidecar JSON рядом с .onnx
        names_json = model_path.with_suffix(".json")
        if names_json.exists():
            try:
                data = json.loads(names_json.read_text("utf-8"))
                names_dict = data.get("names", {})
                if names_dict:
                    return {int(k): v for k, v in names_dict.items()}
            except Exception:
                pass

        logger.warning("Не удалось загрузить классы для %s", model_path)
        return {}

    def predict(
        self,
        image_path: Path,
        confidence: float = 0.25,
    ) -> DetectionResult:
        """Выполняет инференс и возвращает DetectionResult."""
        if not image_path.exists():
            raise FileNotFoundError(f"Изображение не найдено: {image_path}")

        start_time = time.perf_counter()

        # Загрузка и preprocessing
        img = cv2.imread(str(image_path))
        if img is None:
            raise ValueError(f"Не удалось загрузить изображение: {image_path}")

        blob, scale, pad_w, pad_h = self._preprocess(img)

        # Inference
        ort_inputs = {self._input_name: blob}
        ort_outputs = self._session.run(self._output_names, ort_inputs)

        # Postprocessing
        detections = self._postprocess(
            ort_outputs,
            confidence,
            scale,
            pad_w,
            pad_h,
            img.shape[1],  # original width
            img.shape[0],  # original height
        )

        inference_time = time.perf_counter() - start_time

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

    # ------------------------------------------------------------------
    # Preprocessing
    # ------------------------------------------------------------------

    @staticmethod
    def _preprocess(img: np.ndarray) -> tuple[np.ndarray, float, int, int]:
        """Letterbox resize + normalize.

        Returns:
            blob: input tensor [1, 3, H, W] float32
            scale: scale factor
            pad_w: padding (left)
            pad_h: padding (top)
        """
        h, w = img.shape[:2]
        target = 640  # стандартный размер YOLO

        scale = min(target / h, target / w)
        new_w = int(w * scale)
        new_h = int(h * scale)

        resized = cv2.resize(img, (new_w, new_h))

        # Letterbox padding (центрируем)
        pad_w = (target - new_w) // 2
        pad_h = (target - new_h) // 2
        canvas = np.full((target, target, 3), 114, dtype=np.uint8)
        canvas[pad_h: pad_h + new_h, pad_w: pad_w + new_w] = resized

        # BGR -> RGB
        canvas = cv2.cvtColor(canvas, cv2.COLOR_BGR2RGB)

        # Normalize [0, 1]
        blob = canvas.astype(np.float32) / 255.0

        # HWC -> CHW
        blob = np.transpose(blob, (2, 0, 1))

        # Add batch dimension
        blob = np.expand_dims(blob, axis=0)

        return blob, scale, pad_w, pad_h

    # ------------------------------------------------------------------
    # Postprocessing
    # ------------------------------------------------------------------

    def _postprocess(
        self,
        ort_outputs: list[np.ndarray],
        conf_thres: float,
        scale: float,
        pad_w: int,
        pad_h: int,
        orig_w: int,
        orig_h: int,
    ) -> tuple[Detection, ...]:
        """Декодирует ONNX output в DetectionResult.

        Формат выхода Ultralytics YOLO v8 (non-NMS):
            [1, 4 + C, N]
            где C = num_classes, N = num_anchors (8400 для imgsz=640)
            row[0:4] = cx, cy, w, h (в padded-пространстве)
            row[4:] = class probabilities (УЖЕ sigmoid-activated, [0, 1])

        Важно: Ultralytics ONNX export применяет sigmoid на выходе.
        Значения class logits уже являются вероятностями.
        Bbox декодируется из [cx, cy, w, h] -> [x1, y1, x2, y2].
        """
        if len(ort_outputs) != 1:
            logger.warning(
                "Ожидается 1 выход, получено %d", len(ort_outputs)
            )
            return ()

        out = ort_outputs[0]  # [1, 4+C, N]
        num_classes = len(self._classes)

        # Transpose: [1, N, 4+C]
        out = out.transpose(0, 2, 1)

        # Собираем кандидатов
        boxes_raw: list[tuple[float, float, float, float, int, float]] = []

        for i in range(out.shape[1]):
            row = out[0, i]
            bbox_raw = row[:4]  # cx, cy, w, h
            class_probs = row[4:]  # Уже вероятности [0, 1]

            class_id = int(np.argmax(class_probs))
            conf = float(class_probs[class_id])

            if conf < conf_thres:
                continue

            # Decode bbox: [cx, cy, w, h] -> [x1, y1, x2, y2]
            cx, cy, bw, bh = bbox_raw
            x1_pad = cx - bw / 2
            y1_pad = cy - bh / 2
            x2_pad = cx + bw / 2
            y2_pad = cy + bh / 2

            # Undo letterbox: переводим координаты в исходное изображение
            x1 = (x1_pad - pad_w) / scale
            y1 = (y1_pad - pad_h) / scale
            x2 = (x2_pad - pad_w) / scale
            y2 = (y2_pad - pad_h) / scale

            # Clamp к границам
            x1 = max(0.0, min(x1, float(orig_w)))
            y1 = max(0.0, min(y1, float(orig_h)))
            x2 = max(0.0, min(x2, float(orig_w)))
            y2 = max(0.0, min(y2, float(orig_h)))

            # Пропускаем невалидные bbox
            if x2 <= x1 or y2 <= y1:
                continue

            boxes_raw.append((x1, y1, x2, y2, class_id, conf))

        # NMS
        boxes_raw = self._nms(boxes_raw, iou_thres=0.45)

        # Преобразуем в Detection
        detections: list[Detection] = []
        for x1, y1, x2, y2, class_id, conf in boxes_raw:
            class_name = self._classes.get(class_id, str(class_id))
            detections.append(
                Detection(
                    class_id=class_id,
                    class_name=class_name,
                    confidence=conf,
                    bbox=BoundingBox(x1=x1, y1=y1, x2=x2, y2=y2),
                )
            )

        return tuple(detections)

    # ------------------------------------------------------------------
    # NMS
    # ------------------------------------------------------------------

    @staticmethod
    def _nms(
        boxes: list[tuple[float, float, float, float, int, float]],
        iou_thres: float = 0.45,
    ) -> list[tuple[float, float, float, float, int, float]]:
        """Non-Maximum Suppression.

        Args:
            boxes: list of (x1, y1, x2, y2, class_id, confidence)

        Returns:
            Filtered list after NMS.
        """
        if not boxes:
            return []

        # Сортируем по confidence (по убыванию)
        boxes_sorted = sorted(boxes, key=lambda b: b[5], reverse=True)
        keep: list[tuple[float, float, float, float, int, float]] = []

        for box in boxes_sorted:
            x1, y1, x2, y2, cid, conf = box
            area = (x2 - x1) * (y2 - y1)

            # Проверяем IoU с уже оставленными
            override = False
            for kept in keep:
                kx1, ky1, kx2, ky2, kcid, kconf = kept

                # Пересечение
                ix1 = max(x1, kx1)
                iy1 = max(y1, ky1)
                ix2 = min(x2, kx2)
                iy2 = min(y2, ky2)
                iw = max(0.0, ix2 - ix1)
                ih = max(0.0, iy2 - iy1)
                inter = iw * ih

                union = area + (kx2 - kx1) * (ky2 - ky1) - inter
                if union > 0:
                    iou = inter / union
                    if iou > iou_thres:
                        override = True
                        break

            if not override:
                keep.append(box)

        return keep
