# Anomaly Detector

Система обнаружения аномалий на изображениях с использованием ONNX Runtime. Приложение обеспечивает автоматическую классификацию изображений по категориям дефектов, визуализацию результатов с bounding boxes и формирование детализированных отчётов.

## Возможности

- **ONNX Runtime** — высокопроизводительный инференс через ONNX Runtime (CPU)
- **Выбор модели** — поддержка ONNX-моделей (.onnx)
- **Выбор папки изображений** — пакетная обработка директории с фотографиями
- **Настройка confidence** — настраиваемый порог уверенности детекции (0.0–1.0)
- **Multi-class detection** — изображение может быть отнесено к нескольким классам дефектов одновременно
- **Bounding boxes** — отрисовка рамок обнаруженных объектов на сохранённых изображениях
- **Автоматическая сортировка** — изображения сохраняются в каталоги по классам дефектов
- **Excel-отчёты** — детальная и сводная статистика в формате .xlsx
- **Локальная/offline работа** — все вычисления выполняются локально, без подключения к интернету

## Архитектура

```
EntryPoint → UI → Pipeline → Predictor → Detector → ONNX Runtime
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
│   │   ├── detector.py         # Адаптер ONNX Runtime
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
├── tools/                      # Development-инструменты
│   ├── export_to_onnx.py       # Экспорт .pt → .onnx
│   ├── pyproject.toml          # Dev-зависимости (ultralytics)
│   ├── .venv/                  # Окружение для экспорта
│   └── run_export.bat          # Скрипт запуска экспорта
├── tests/                      # Тесты
│   ├── test_onnx.py            # Regression test PT vs ONNX
│   └── test_production_onnx.py # Production ONNX runtime test
├── models/                     # ONNX-модели (.onnx)
│   ├── best.onnx               # Модель
│   └── best.json               # Имена классов (sidecar)
├── data/                       # Рабочие данные
│   ├── database/               # База данных
│   ├── output/                 # Результаты детекции
│   ├── reports/                # Excel-отчёты
│   └── logs/                   # Логи приложения
├── run.bat                     # Скрипт запуска приложения
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

ONNX-модели помещаются в корневую папку `models/`:

```
anomaly-detector/
└── models/
    ├── best.onnx
    └── best.json
```

Поддерживаемый формат: **`.onnx`**.

Файл `.json` рядом с `.onnx` содержит имена классов (sidecar). Если классы уже встроены в ONNX metadata, `.json` создаётся автоматически скриптом экспорта.

### Development-инструменты (`tools/`)

Папка `tools/` содержит утилиты для разработки и экспорта моделей из YOLO (PyTorch) в формат ONNX, который используется приложением.

| Файл | Описание |
|------|----------|
| `export_to_onnx.py` | Python-скрипт экспорта YOLO-модели (.pt) в ONNX (.onnx) |
| `run_export.bat` | Интерактивный батник для запуска экспорта |
| `pyproject.toml` | Dev-зависимости (ultralytics, onnxruntime) |
| `.venv/` | Изолированное окружение Python для экспорта |

#### `export_to_onnx.py` — экспорт модели

Конвертирует YOLO-модель из формата PyTorch (`.pt`) в ONNX (`.onnx`), проверяет корректность через ONNX Runtime и создаёт sidecar-файл с именами классов.

**Использование:**

```powershell
cd anomaly-detector\tools
python export_to_onnx.py ..\models\best.pt
```

С параметрами:

```powershell
python export_to_onnx.py ..\models\best.pt --output ..\models\new_model.onnx --imgsz 640
```

**Параметры:**

| Параметр | Описание | По умолчанию |
|----------|----------|:---:|
| `model_pt` | Путь к модели `.pt` | (обязательный) |
| `--output`, `-o` | Путь для выходного `.onnx` | Рядом с `.pt` |
| `--imgsz` | Размер входа модели | `640` |

Скрипт автоматически использует Python из `tools/.venv/`.

#### `run_export.bat` — интерактивный запуск

Удобный способ запуска экспорта: двойным кликом открывается консоль, куда вводится путь к модели.

**Использование:**

```powershell
cd anomaly-detector\tools
run_export.bat
```

После запуска появится запрос:

```
Enter path to model (.pt): ..\models\best.pt
```

Введите путь и нажмите Enter — скрипт выполнит экспорт.

Также можно передать путь через аргумент:

```powershell
run_export.bat ..\models\best.pt
```

**Что делает скрипт:**

1. Загружает модель через Ultralytics YOLO
2. Экспортирует в ONNX с упрощением (simplify)
3. Проверяет корректность через ONNX Runtime
4. Создаёт sidecar `.json` с именами классов
5. Выводит размеры файлов, входные/выходные тензоры и статус `EXPORT: PASS / FAIL`

## Данные

Все результаты работы приложения сохраняются в `data/`:

- **data/output/** — отсортированные изображения по классам дефектов
- **data/reports/** — Excel-отчёты
- **data/logs/** — логи приложения
- **data/database/** — база данных

Каталоги `data/` и `models/` не включены в Git-репозиторий.

## Разработка

Проект использует `uv` для управления зависимостями.

### Runtime (приложение)

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

### Dev-инструменты (экспорт моделей)

```powershell
# Экспорт модели в ONNX
cd tools
python export_to_onnx.py ..\models\best.pt

# Добавление dev-зависимости
uv pip install -p .venv\Scripts\python.exe <package-name>
```

## Сборка EXE

Проект подготовлен к сборке в portable `.exe` с помощью PyInstaller или аналогичных инструментов.

Ожидаемая структура после сборки:

```
AnomalyDetector/
├── AnomalyDetector.exe
├── models/
│   └── *.onnx
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
