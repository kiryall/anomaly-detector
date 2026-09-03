# Anomaly Detector

Система обнаружения аномалий на изображениях с использованием YOLO-моделей. Приложение обеспечивает автоматическую классификацию изображений по категориям дефектов, визуализацию результатов с bounding boxes и формирование детализированных отчётов.

## Возможности

- **YOLO detection** — использование моделей Ultralytics YOLO для обнаружения аномалий
- **Выбор модели** — поддержка нескольких YOLO-моделей (.pt, .pth, .onnx)
- **Выбор папки изображений** — пакетная обработка директории с фотографиями
- **Настройка confidence** — настраиваемый порог уверенности детекции (0.0–1.0)
- **Multi-class detection** — изображение может быть отнесено к нескольким классам дефектов одновременно
- **Bounding boxes** — отрисовка рамок обнаруженных объектов на сохранённых изображениях
- **Автоматическая сортировка** — изображения сохраняются в каталоги по классам дефектов
- **Excel-отчёты** — детальная и сводная статистика в формате .xlsx
- **Локальная/offline работа** — все вычисления выполняются локально, без подключения к интернету

## Архитектура

```
EntryPoint → UI → Pipeline → Predictor → Detector → YOLO
```

Модули:

- **entrypoint** — точка входа (`main.py`, `bootstrap.py`)
- **ui** — NiceGUI-интерфейс (`MainWindow`)
- **core** — ядро: `Pipeline`, `Predictor`, `Detector`, `ModelManager`
- **io** — ввод-вывод: `ImageScanner`
- **reports** — отчёты: `ReportService`
- **config** — конфигурация: `Settings`, `Paths`, `UserSettings`
- **services** — сервисы: `state`, `logger`
- **schemas** — схемы данных: `Detection`, `DetectionResult`, `BoundingBox`

## Структура проекта

```
anomaly-detector/
├── app/                        # Исходный код приложения
│   ├── entrypoint/             # Точка входа
│   │   ├── main.py             # Точка входа (run.bat, uv run)
│   │   ├── __main__.py         # Запуск через python -m app
│   │   └── bootstrap.py        # Инициализация и связывание компонентов
│   ├── ui/                     # Пользовательский интерфейс
│   │   └── ui.py               # NiceGUI-интерфейс (MainWindow)
│   ├── core/                   # Ядро приложения
│   │   ├── pipeline.py         # Pipeline обработки изображений
│   │   ├── predictor.py        # Сервис предсказаний
│   │   ├── detector.py         # Адаптер YOLO
│   │   └── model_manager.py    # Управление моделями
│   ├── io/                     # Ввод-вывод
│   │   └── image_scanner.py    # Сканирование папки изображений
│   ├── reports/                # Отчёты
│   │   └── report.py           # Формирование Excel-отчётов
│   ├── config/                 # Конфигурация
│   │   ├── settings.py         # Settings (Pydantic)
│   │   ├── paths.py            # Пути (dev/EXE режимы)
│   │   └── models.py           # UserSettings, SUPPORTED_EXTENSIONS
│   ├── services/               # Сервисы
│   │   ├── state.py            # Состояние приложения
│   │   └── logger.py           # Логирование
│   ├── schemas/                # Схемы данных
│   │   └── detection.py        # Detection, DetectionResult, BoundingBox
│   ├── pyproject.toml          # Зависимости Python
│   └── uv.lock                 # Блок зависимостей
├── models/                     # YOLO-модели (.pt)
├── data/                       # Рабочие данные
│   ├── database/               # База данных
│   ├── output/                 # Результаты детекции
│   ├── reports/                # Excel-отчёты
│   └── logs/                   # Логи приложения
├── run.bat                     # Скрипт запуска
├── README.md                   # Документация для разработчиков
└── USER_GUIDE.md               # Инструкция пользователя
```

## Требования

- **Python 3.11+**
- **uv** — менеджер пакетов и запуска ([install](https://docs.astral.sh/uv/getting-started/installation/))
- Зависимости описаны в `app/pyproject.toml`

## Установка

```powershell
cd anomaly-detector\app
uv sync
```

Это установит все зависимости из `pyproject.toml` в изолированное окружение.

## Запуск

```powershell
cd anomaly-detector
.\run.bat
```

Приложение запустится по адресу `http://127.0.0.1:8080`.

## Модели

YOLO-модели помещаются в корневую папку `models/`:

```
anomaly-detector/
└── models/
    ├── best.pt
    └── new_model.pt
```

Поддерживаемые форматы: `.pt`, `.pth`, `.onnx`.

После размещения новой модели — обновите список в интерфейсе или перезапустите приложение.

## Данные

Все результаты работы приложения сохраняются в `data/`:

- **data/output/** — отсортированные изображения по классам дефектов
- **data/reports/** — Excel-отчёты
- **data/logs/** — логи приложения
- **data/database/** — база данных

Каталоги `data/` и `models/` не включены в Git-репозиторий.

## Разработка

Проект использует `uv` для управления зависимостями. Все зависимости находятся в `app/pyproject.toml`.

```powershell
# Установка зависимостей
cd app
uv sync

# Запуск в режиме разработки
uv run --directory app python entrypoint/main.py

# Или из корня проекта
uv run --directory app python -m app

# Добавление новой зависимости
uv add <package-name>
```

## Сборка EXE

Проект подготовлен к сборке в portable `.exe` с помощью PyInstaller или аналогичных инструментов.

Ожидаемая структура после сборки:

```
AnomalyDetector/
├── AnomalyDetector.exe
├── models/
│   └── *.pt
└── data/
    ├── database/
    ├── output/
    ├── reports/
    └── logs/
```

В режиме EXE пути автоматически переключаются:
- Корень приложения = `Path(sys.executable).parent`
- Модели и данные находятся рядом с `.exe`

## License

MIT
