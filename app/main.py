# app/main.py
# Точка входа приложения.

from __future__ import annotations

import sys
from pathlib import Path

# pyproject.toml находится в app/, поэтому при запуске из app/
# sys.path[0] = app/, и import app не работает.
# Добавляем корень проекта в начало sys.path.
_project_root = Path(__file__).resolve().parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

from app.bootstrap import Bootstrap


def main() -> None:
    bootstrap = Bootstrap()
    bootstrap.run()
    from app.ui import MainWindow
    window = MainWindow(
        model_manager=bootstrap.model_manager,
        pipeline=bootstrap.pipeline,
        report_service=bootstrap.report_service,
    )
    window.run()


if __name__ == "__main__":
    main()
