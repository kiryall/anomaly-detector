from __future__ import annotations

from app.config.settings import settings
from app.model_manager import ModelManager


class Bootstrap:

    def run(self):
        """Инициализация приложения."""
        self.create_directories()

        self.load_settings()

        self.init_model_manager()

        self.configure_logger()

        self.init_database()

        self.discover_models()

    def create_directories(self):
        """Создание необходимых директорий."""
        for directory in settings.paths.directories:
            directory.mkdir(parents=True, exist_ok=True)

    def load_settings(self):
        """Загрузка настроек пользователя."""
        settings.load_settings()

    def init_model_manager(self):
        """Инициализация менеджера моделей."""
        self.model_manager = ModelManager()

    def configure_logger(self):
        """Настройка логирования."""
        from app.services.logger import logger

        self.logger = logger
        self.logger.info("Приложение запущено")

    def init_database(self):

        ...

    def discover_models(self):

        ...