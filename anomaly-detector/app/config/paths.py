import sys
from pathlib import Path


class Paths:

    def __init__(self):

        if getattr(sys, "frozen", False):
            self.root = Path(sys.executable).parent
        else:
            self.root = Path(__file__).resolve().parents[2]

        self.config = self.root / "config"

        self.models = self.root / "models"

        self.data = self.root / "data"

        self.database = self.data / "database"

        self.output = self.data / "output"

        self.reports = self.data / "reports"

        self.logs = self.data / "logs"

        self.settings = self.config / "settings.json"

    def get_model_output_root(self, model_name: str) -> Path:
        """Возвращает корневую выходную директорию для модели."""
        return self.output / f"output_{model_name}"

    def get_output_dir(self, model_name: str, class_name: str) -> Path:
        """Возвращает путь к выходной директории для заданной модели и класса."""
        return self.get_model_output_root(model_name) / class_name

    @property
    def directories(self):

        return [

            self.config,

            self.models,

            self.data,

            self.database,

            self.output,

            self.reports,

            self.logs,

        ]