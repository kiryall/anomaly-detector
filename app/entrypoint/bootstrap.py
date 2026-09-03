from __future__ import annotations

from app.config.settings import settings
from app.io.image_scanner import ImageScanner
from app.core.model_manager import ModelManager
from app.core.pipeline import Pipeline
from app.core.predictor import Predictor
from app.reports.report import ReportService


class Bootstrap:

    def run(self):
        """Инициализация приложения."""
        self.create_directories()

        self.load_settings()

        self.init_model_manager()

        self.configure_logger()

        self.init_database()

        self.discover_models()

        self.init_predictor()

        self.init_image_scanner()

        self.init_pipeline()

        self.init_report_service()

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

    def init_predictor(self):
        """Инициализация Predictor."""
        self.predictor = Predictor()

    def init_image_scanner(self):
        """Инициализация ImageScanner."""
        self.image_scanner = ImageScanner()

    def init_pipeline(self):
        """Инициализация Pipeline."""
        self.pipeline = Pipeline(
            image_scanner=self.image_scanner,
            paths=settings.paths,
        )

    def init_report_service(self):
        """Инициализация ReportService."""
        self.report_service = ReportService()
