#!/usr/bin/env python3
"""Экспорт YOLO-модели PyTorch (.pt) в ONNX (.onnx).

Использование:
    python tools/export_to_onnx.py models/best.pt
    python tools/export_to_onnx.py models/best.pt --output models/best.onnx

НЕ является частью приложения. Только для development.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

# ------------------------------------------------------------------
# Auto-detect tools/.venv Python (uses dev dependencies: ultralytics)
# ------------------------------------------------------------------

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
_TOOLS_VENV = _PROJECT_ROOT / "tools" / ".venv" / "Scripts" / "python.exe"


def _reexec_in_tools_venv() -> None:
    """Re-launches itself through tools/.venv Python if not already in it."""
    if _TOOLS_VENV.exists():
        try:
            venv_abs = _TOOLS_VENV.resolve()
            current_abs = Path(sys.executable).resolve()
            if current_abs == venv_abs:
                return  # Already in venv
        except (OSError, ValueError):
            pass

        # Re-launch via tools/.venv Python
        args = [str(_TOOLS_VENV)] + sys.argv
        result = subprocess.run(args)
        sys.exit(result.returncode)


# Auto-reexec if not in tools/.venv
_reexec_in_tools_venv()

# Fix Windows console encoding for Unicode
if sys.platform == "win32":
    import codecs

    sys.stdout = codecs.getwriter("utf-8")(sys.stdout.buffer, "strict")
    sys.stderr = codecs.getwriter("utf-8")(sys.stderr.buffer, "strict")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Экспорт YOLO-модели PyTorch в ONNX"
    )
    parser.add_argument(
        "model_pt",
        type=str,
        help="Путь к модели .pt (например, models/best.pt)",
    )
    parser.add_argument(
        "--output",
        "-o",
        type=str,
        default=None,
        help="Путь для выходного .onnx (по умолчанию: рядом с .pt)",
    )
    parser.add_argument(
        "--imgsz",
        type=int,
        default=640,
        help="Размер входа модели (по умолчанию: 640)",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    model_pt = Path(args.model_pt).resolve()
    imgsz = args.imgsz

    # ------------------------------------------------------------------
    # 1. Проверка существования .pt
    # ------------------------------------------------------------------
    print(f"Model: {model_pt}")

    if not model_pt.exists():
        print(f"\nERROR: файл не найден: {model_pt}")
        print("EXPORT: FAIL")
        return 1

    if not model_pt.is_file():
        print(f"\nERROR: путь не является файлом: {model_pt}")
        print("EXPORT: FAIL")
        return 1

    # Определяем выходной путь
    if args.output:
        model_onnx = Path(args.output).resolve()
    else:
        model_onnx = model_pt.with_suffix(".onnx")

    # ------------------------------------------------------------------
    # 2. Загрузка модели
    # ------------------------------------------------------------------
    print()
    from ultralytics import YOLO

    print("Loading model...")
    model = YOLO(str(model_pt))
    model_type = getattr(model.model, "task", "detect")
    print(f"Model type: {model_type}")

    # ------------------------------------------------------------------
    # 3. Классы модели
    # ------------------------------------------------------------------
    classes: dict[int, str] = {}
    if hasattr(model.model, "names") and model.model.names:
        classes = model.model.names
    print("\nClasses:")
    for cid, cname in sorted(classes.items()):
        print(f"  {cid}: {cname}")

    # ------------------------------------------------------------------
    # 4. Экспорт в ONNX
    # ------------------------------------------------------------------
    print(f"\nExporting to ONNX (imgsz={imgsz})...")

    model.export(
        format="onnx",
        imgsz=imgsz,
        simplify=True,
    )

    # ------------------------------------------------------------------
    # 5. Проверка наличия .onnx
    # ------------------------------------------------------------------
    # Ultralytics сохраняет экспорт рядом с .pt с тем же именем
    # (игнорирует --output), поэтому проверяем оба пути
    onnx_default = model_pt.with_suffix(".onnx")
    
    if not model_onnx.exists() and not onnx_default.exists():
        print(f"\nERROR: файл не создан")
        print("EXPORT: FAIL")
        return 1

    # Используем существующий файл
    if model_onnx.exists():
        print(f"\nONNX: {model_onnx}")
    else:
        print(f"\nONNX: {onnx_default} (Ultralytics игнорирует --output)")
        model_onnx = onnx_default

    # ------------------------------------------------------------------
    # 6. Загрузка через ONNX Runtime и вывод метаданных
    # ------------------------------------------------------------------
    import onnxruntime as ort

    session = ort.InferenceSession(str(model_onnx))

    print("\nONNX inputs:")
    for inp in session.get_inputs():
        print(f"  {inp.name}")
        print(f"    shape={inp.shape}")
        print(f"    dtype={inp.type}")

    print("\nONNX outputs:")
    for out in session.get_outputs():
        print(f"  {out.name}")
        print(f"    shape={out.shape}")
        print(f"    dtype={out.type}")

    # ------------------------------------------------------------------
    # 7. Размеры файлов
    # ------------------------------------------------------------------
    pt_size_mb = model_pt.stat().st_size / (1024 * 1024)
    onnx_size_mb = model_onnx.stat().st_size / (1024 * 1024)
    print(f"\nPT size:   {pt_size_mb:.1f} MB")
    print(f"ONNX size: {onnx_size_mb:.1f} MB")

    # ------------------------------------------------------------------
    # 8. Создание sidecar JSON для class names (если нужно)
    # ------------------------------------------------------------------
    names_json = model_onnx.with_suffix(".json")
    meta = session.get_modelmeta().custom_metadata_map
    names_raw = meta.get("names", "")

    if names_raw:
        try:
            loaded_classes = eval(names_raw)  # noqa: S307
            if loaded_classes and isinstance(loaded_classes, dict):
                print(f"\nClass names found in ONNX metadata: {loaded_classes}")
                # Сохраняем sidecar для надёжности
                with open(names_json, "w", encoding="utf-8") as f:
                    json.dump({"names": loaded_classes}, f, ensure_ascii=False, indent=2)
                print(f"Sidecar saved: {names_json}")
        except Exception:
            pass
    else:
        print("\nWARNING: class names NOT found in ONNX metadata")
        # Сохраняем sidecar из PT
        with open(names_json, "w", encoding="utf-8") as f:
            json.dump({"names": {str(k): v for k, v in classes.items()}}, f, ensure_ascii=False, indent=2)
        print(f"Sidecar created from PT: {names_json}")

    # ------------------------------------------------------------------
    # 9. Итоговый статус
    # ------------------------------------------------------------------
    print()
    print("EXPORT: PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
