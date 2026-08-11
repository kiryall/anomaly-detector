from __future__ import annotations

from pathlib import Path

SUPPORTED_EXTENSIONS = {
        ".jpg",
        ".jpeg",
        ".png",
        ".bmp",
        ".tif",
        ".tiff",
        ".webp",
    }

class ImageScanner:
    """Сканирует папку и находит изображения."""

    SUPPORTED_EXTENSIONS = SUPPORTED_EXTENSIONS
    def scan(self, folder: Path) -> list[Path]:
        """
        Возвращает список изображений в указанной папке.

        Args:
            folder: Папка с изображениями.

        Returns:
            Список путей к изображениям.
        """

        if not folder.exists():
            raise FileNotFoundError(
                f"Папка не существует: {folder}"
            )

        if not folder.is_dir():
            raise NotADirectoryError(
                f"Указанный путь не является папкой: {folder}"
            )

        images = [
            file
            for file in folder.iterdir()
            if file.is_file()
            and file.suffix.lower() in self.SUPPORTED_EXTENSIONS
        ]

        return sorted(images)