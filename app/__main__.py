"""Позволяет запускать пакет через: python -m app."""

from __future__ import annotations

import importlib.util
from pathlib import Path


def _run() -> None:
    """Загружает top-level app.py без конфликтов с пакетом app/."""

    project_root = Path(__file__).parents[1]
    app_py = project_root / "app.py"

    spec = importlib.util.spec_from_file_location("_app_runner", app_py)
    if spec is None or spec.loader is None:
        raise ImportError(f"Не удалось загрузить модуль: {app_py}")

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.main()


if __name__ == "__main__":
    _run()
