# app.py
# Основной файл приложения, который запускает процесс инициализации и запуска пользовательского интерфейса.

from app.bootstrap import Bootstrap
from app.ui import MainWindow


def main() -> None:

    bootstrap = Bootstrap()

    bootstrap.run()

    window = MainWindow(
        model_manager=bootstrap.model_manager,
    )

    window.run()


if __name__ == "__main__":
    main()