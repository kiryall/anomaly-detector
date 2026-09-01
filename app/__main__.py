"""Позволяет запускать пакет через: python -m app."""

from __future__ import annotations

from app.main import main


def _run() -> None:
    """Запускает точку входа приложения."""
    main()


if __name__ == "__main__":
    _run()
