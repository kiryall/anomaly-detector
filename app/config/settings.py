from __future__ import annotations

from pydantic import ValidationError

from .models import UserSettings
from .paths import Paths


class Settings:
    def __init__(self):

        self.paths = Paths()

        self.user = UserSettings()

    def load_settings(self):
        """Загрузка настроек пользователя из файла settings.json."""

        if not self.paths.settings.exists():
            self.save_settings()

            return

        try:
            self.user = UserSettings.model_validate_json(
                self.paths.settings.read_text("utf-8")
            )

        except ValidationError:
            self.user = UserSettings()

            self.save_settings()

    def save_settings(self):
        """Сохранение настроек пользователя в файл settings.json."""

        self.paths.settings.write_text(
            self.user.model_dump_json(indent=4),
            encoding="utf-8",
        )


settings = Settings()