from __future__ import annotations

from pathlib import Path
from tkinter import Tk, filedialog

from nicegui import ui

from app.config.settings import settings
from app.image_scanner import ImageScanner
from app.model_manager import ModelManager
from app.services.state import state


class MainWindow:
    """Главное окно приложения."""

    def __init__(
        self,
        model_manager: ModelManager,
    ) -> None:

        self.model_manager = model_manager
        self.image_scanner = ImageScanner()

        # UI elements
        self.model_select = None
        self.folder_label = None
        self.image_count_label = None
        self.start_button = None
        self.report_button = None
        self.status_label = None
        self.progress_bar = None
        self.progress_label = None

    # =====================================================
    # BUILD
    # =====================================================

    def build(self) -> None:
        """Создаёт интерфейс."""

        ui.page_title("Anomaly Detector")

        with ui.column().classes("w-full max-w-2xl mx-auto p-6 gap-4"):
            ui.label("Anomaly Detector").classes("text-2xl font-bold")

            self.build_model_block()

            self.build_folder_block()

            ui.separator()

            self.build_detection_block()

            self.build_status_block()

            self.build_statistics_block()

            self.build_report_block()

    # =====================================================
    # MODEL
    # =====================================================

    def build_model_block(self) -> None:
        """Блок выбора модели."""

        with ui.row().classes("w-full items-center"):
            ui.label("Модель").classes("w-24")

            default_model_name = settings.user.model
            default_model_info = (
                self.model_manager.get_model(default_model_name)
                if default_model_name
                else None
            )
            default_model = (
                default_model_info.display_name if default_model_info else None
            )

            self.model_select = ui.select(
                options=self.model_manager.names,
                value=default_model,
                label="Выберите модель",
                on_change=self.on_model_changed,
            ).classes("flex-1")

        if default_model:
            state.selected_model = default_model

    # =====================================================
    # FOLDER
    # =====================================================

    def build_folder_block(self) -> None:
        """Блок выбора папки."""

        with ui.row().classes("w-full items-center"):
            ui.label("Папка").classes("w-24")

            self.folder_label = ui.label("Не выбрана").classes(
                "flex-1 truncate text-gray-500"
            )

            ui.button(
                "Выбрать",
                on_click=self.choose_folder,
            )

        self.image_count_label = ui.label("Изображения не выбраны").classes(
            "text-sm text-gray-500 ml-24"
        )

    # =====================================================
    # DETECTION
    # =====================================================

    def build_detection_block(self) -> None:
        """Кнопка запуска детекции."""

        self.start_button = ui.button(
            "Начать детекцию",
            on_click=self.start_detection,
        ).classes("w-full")

        self.update_start_button()

    # =====================================================
    # STATUS
    # =====================================================

    def build_status_block(self) -> None:
        """Статус и прогресс."""

        self.status_label = ui.label(state.status).classes("text-sm")

        self.progress_bar = ui.linear_progress(value=0).classes("w-full")

        self.progress_label = ui.label("0 / 0").classes("text-sm text-gray-500")

    # =====================================================
    # STATISTICS
    # =====================================================

    def build_statistics_block(self) -> None:
        """Статистика обработки."""

        with ui.row().classes("w-full justify-between text-sm"):
            self.anomaly_label = ui.label("Аномалии: 0")

            self.normal_label = ui.label("Норма: 0")

            self.errors_label = ui.label("Ошибки: 0")

    # =====================================================
    # REPORT
    # =====================================================

    def build_report_block(self) -> None:
        """Кнопка сохранения отчёта."""

        self.report_button = ui.button(
            "Сохранить отчёт",
            on_click=self.save_report,
        ).classes("w-full")

        self.report_button.disable()

    # =====================================================
    # MODEL HANDLER
    # =====================================================

    def on_model_changed(self, event) -> None:
        """Обрабатывает выбор модели."""

        model_name = event.value

        if not model_name:
            state.selected_model = ""
            self.update_start_button()
            return

        if not self.model_manager.exists(model_name):
            ui.notify(
                "Выбранная модель не найдена.",
                type="negative",
            )
            return

        state.selected_model = model_name

        settings.user.model = model_name
        settings.save_settings()

        ui.notify(
            f"Выбрана модель: {model_name}",
            type="positive",
        )

        self.update_start_button()

    # =====================================================
    # FOLDER HANDLER
    # =====================================================

    def choose_folder(self) -> None:
        """Выбирает папку с фотографиями."""

        root = Tk()
        root.withdraw()
        root.attributes("-topmost", True)

        folder = filedialog.askdirectory(title="Выберите папку с фотографиями")

        root.destroy()

        if not folder:
            return

        folder_path = Path(folder)

        try:
            images = self.image_scanner.scan(folder_path)

        except (
            FileNotFoundError,
            NotADirectoryError,
            PermissionError,
            OSError,
        ) as error:
            ui.notify(
                f"Не удалось прочитать папку: {error}",
                type="negative",
            )

            return

        if not images:
            state.selected_folder = None
            state.images.clear()
            state.statistics.reset()

            self.folder_label.set_text(str(folder_path))

            self.image_count_label.set_text("Поддерживаемые изображения не найдены")

            self.status_label.set_text("Папка не готова к обработке")

            self.update_start_button()

            ui.notify(
                "В выбранной папке нет изображений.",
                type="warning",
            )

            return

        # Сохраняем состояние

        state.selected_folder = folder_path
        state.images = images

        state.statistics.reset()
        state.statistics.total_images = len(images)

        state.status = "Готов к детекции"

        # Обновляем UI

        self.folder_label.set_text(str(folder_path))

        self.image_count_label.set_text(f"Изображений: {len(images)}")

        self.status_label.set_text(state.status)

        self.progress_bar.set_value(0)

        self.progress_label.set_text(f"0 / {len(images)}")

        self.update_statistics()

        self.update_start_button()

        ui.notify(
            f"Найдено изображений: {len(images)}",
            type="positive",
        )

    # =====================================================
    # BUTTON STATE
    # =====================================================

    def update_start_button(self) -> None:
        """Обновляет состояние кнопки детекции."""

        if self.start_button is None:
            return

        can_start = (
            bool(state.selected_model)
            and state.selected_folder is not None
            and len(state.images) > 0
            and not state.is_processing
        )

        if can_start:
            self.start_button.enable()
        else:
            self.start_button.disable()

    # =====================================================
    # DETECTION
    # =====================================================

    async def start_detection(self) -> None:
        """Запускает детекцию."""

        if not state.selected_model:
            ui.notify(
                "Выберите модель.",
                type="warning",
            )
            return

        if state.selected_folder is None:
            ui.notify(
                "Выберите папку с фотографиями.",
                type="warning",
            )
            return

        if not state.images:
            ui.notify(
                "В папке нет изображений.",
                type="warning",
            )
            return

        state.is_processing = True
        state.status = "Идёт детекция..."

        self.status_label.set_text(state.status)

        self.update_start_button()

        try:
            # TODO:
            # Здесь позже будет Pipeline.
            #
            # Пока заглушка.

            for image in state.images:
                await self.process_image_stub(image)

                state.statistics.processed_images += 1

                self.update_progress()

                await ui.run_javascript(
                    "new Promise(resolve => setTimeout(resolve, 10))"
                )

            state.status = "Детекция завершена"

            self.status_label.set_text(state.status)

            self.report_button.enable()

            ui.notify(
                "Детекция завершена.",
                type="positive",
            )

        finally:
            state.is_processing = False

            self.update_start_button()

    async def process_image_stub(
        self,
        image: Path,
    ) -> None:
        """Временная заглушка инференса."""

        # Здесь позже будет YOLO.

        return

    # =====================================================
    # PROGRESS
    # =====================================================

    def update_progress(self) -> None:
        """Обновляет прогресс."""

        statistics = state.statistics

        self.progress_bar.set_value(statistics.progress)

        self.progress_label.set_text(
            f"{statistics.processed_images} / {statistics.total_images}"
        )

        self.update_statistics()

    # =====================================================
    # STATISTICS
    # =====================================================

    def update_statistics(self) -> None:
        """Обновляет статистику."""

        statistics = state.statistics

        self.anomaly_label.set_text(f"Аномалии: {statistics.anomaly_images}")

        self.normal_label.set_text(f"Норма: {statistics.normal_images}")

        self.errors_label.set_text(f"Ошибки: {statistics.errors}")

    # =====================================================
    # REPORT
    # =====================================================

    def save_report(self) -> None:
        """Сохраняет отчёт."""

        # TODO:
        # Здесь позже будет ReportService.

        ui.notify(
            "Формирование отчёта пока не реализовано.",
            type="info",
        )

    # =====================================================
    # RUN
    # =====================================================

    def run(self) -> None:
        """Запускает NiceGUI."""

        self.build()

        ui.run(
            title="Anomaly Detector",
            reload=False,
        )
