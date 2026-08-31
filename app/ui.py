from __future__ import annotations

import asyncio
from pathlib import Path
from tkinter import Tk, filedialog
from typing import TYPE_CHECKING, Any

from nicegui import ui

from app.config.settings import settings
from app.image_scanner import ImageScanner
from app.model_manager import ModelManager
from app.pipeline import Pipeline
from app.services.state import state

if TYPE_CHECKING:
    from nicegui.elements import Label
    from nicegui.elements import Button
    from nicegui.elements import Select
    from nicegui.elements import Number


class MainWindow:
    """Главное окно приложения."""

    # Типизированные UI-элементы — инициализируются в build()
    model_select: Select | None = None
    folder_label: Label | None = None
    image_count_label: Label | None = None
    start_button: Button | None = None
    report_button: Button | None = None
    status_label: Label | None = None
    confidence_input: Number | None = None

    def __init__(
        self,
        model_manager: ModelManager,
        pipeline: Pipeline,
    ) -> None:

        self.model_manager = model_manager
        self.pipeline = pipeline
        self.image_scanner = ImageScanner()

    # =====================================================
    # HELPERS — safe UI updates (никогда не упадёт на None)
    # =====================================================

    def _set_text(
        self,
        label: Label | None,
        text: str,
    ) -> None:
        """Безопасно устанавливает текст label."""
        if label is not None:
            label.set_text(text)


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

            self.build_confidence_block()

            ui.separator()

            self.build_detection_block()

            self.build_status_block()

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
    # CONFIDENCE
    # =====================================================

    def build_confidence_block(self) -> None:
        """Блок выбора порога уверенности."""

        with ui.row().classes("w-full items-center"):
            ui.label("Порог уверенности").classes("w-24")

            self.confidence_input = ui.number(
                format="%.2f",
                min=0.0,
                max=1.0,
                step=0.05,
                value=settings.user.confidence,
                on_change=self.on_confidence_changed,
            ).classes("w-20")


    # =====================================================
    # CONFIDENCE HANDLER
    # =====================================================

    def on_confidence_changed(self, event: Any) -> None:
        """Обрабатывает ручное изменение порога уверенности."""

        if self.confidence_input is not None:
            settings.user.confidence = self.confidence_input.value
            settings.save_settings()

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
        """Статус обработки."""

        initial_text = (
            "Для начала детекции выберите модель и укажите папку с изображениями"
        )

        self.status_label = ui.label(initial_text).classes("text-xl font-bold")

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

    def on_model_changed(self, event: Any) -> None:
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

            self._set_text(self.folder_label, str(folder_path))
            self._set_text(self.image_count_label, "Поддерживаемые изображения не найдены")
            self._set_text(self.status_label, "Папка не готова к обработке")

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

        self._set_text(self.folder_label, str(folder_path))
        self._set_text(self.image_count_label, f"Изображений: {len(images)}")
        self._set_text(self.status_label, state.status)

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

        self._set_text(self.status_label, state.status)

        self.update_start_button()

        try:
            confidence = float(self.confidence_input.value)

            model_info = self.model_manager.get_model(state.selected_model)
            if model_info is None:
                ui.notify(
                    "Не удалось найти выбранную модель.",
                    type="negative",
                )
                return

            results = await asyncio.to_thread(
                self.pipeline.run,
                state.selected_folder,
                model_info.path,
                confidence,
            )

            state.statistics.processed_images = len(results)
            state.statistics.total_images = len(results)

            state.status = "Детекция завершена"

            self._set_text(self.status_label, state.status)

            if self.report_button is not None:
                self.report_button.enable()

            ui.notify(
                f"Детекция завершена. "
                f"Всего: {len(results)}, "
                f"Обнаружено: {state.statistics.anomaly_images}, "
                f"No defect: {state.statistics.normal_images}",
                type="positive",
            )

        except (FileNotFoundError, NotADirectoryError, ValueError, RuntimeError) as error:
            state.status = "Ошибка"
            self._set_text(self.status_label, state.status)

            ui.notify(
                f"Ошибка: {error}",
                type="negative",
            )

        finally:
            state.is_processing = False

            self.update_start_button()

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
