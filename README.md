# Job Instruction Downloader

Универсальное приложение для автоматизации скачивания должностных инструкций и других документов с различных веб-ресурсов с поддержкой множественных облачных хранилищ.

## Обзор проекта

Job Instruction Downloader - это мощное приложение с графическим интерфейсом, предназначенное для автоматизации процесса скачивания документов с таких ресурсов как Consultant.ru, Garant.ru и других веб-сайтов. Приложение поддерживает сохранение файлов в различные облачные хранилища включая Google Drive, OneDrive, Dropbox и Яндекс.Диск.

### Основные возможности

- **Универсальность**: Поддержка любых веб-ресурсов через настраиваемые парсеры
- **Современный GUI**: Интуитивный интерфейс на PyQt6/PySide6
- **Автоматизация**: Полностью автоматизированный процесс скачивания
- **Облачная интеграция**: Поддержка множественных облачных хранилищ
- **Надежность**: Устойчивость к сетевым проблемам и изменениям структуры сайтов
- **Конфигурируемость**: Гибкая настройка через JSON конфигурации

### Поддерживаемые ресурсы

- **Правовые системы**: Consultant.ru, Garant.ru, Kodeks.ru
- **Корпоративные порталы**: SharePoint, Confluence
- **Государственные ресурсы**: Официальные сайты министерств и ведомств
- **Пользовательские сайты**: Любые веб-ресурсы через визуальный конструктор

## Технологический стек

- **Backend**: Python 3.12
- **GUI Framework**: PyQt6/PySide6 (с fallback на Tkinter)
- **Web Automation**: Selenium WebDriver
- **Cloud Storage APIs**: Google Drive, OneDrive, Dropbox, Яндекс.Диск
- **Конфигурация**: JSON/YAML файлы + SQLite для метаданных
- **Логирование**: Python logging с structured logging
- **Парсинг**: BeautifulSoup4, lxml, requests

## Установка

### Требования

- Python 3.12 или выше
- Chrome/Chromium браузер (для Selenium)
- Доступ к интернету

### Установка из исходного кода

```bash
# Клонирование репозитория
git clone https://github.com/CoreTwin/web2-parser-py.git
cd web2-parser-py

# Создание виртуального окружения
python -m venv venv
source venv/bin/activate  # Linux/Mac
# или
venv\Scripts\activate  # Windows

# Установка зависимостей
pip install -r requirements.txt

# Установка пакета в режиме разработки
pip install -e .
```

### Установка через pip (планируется)

```bash
pip install job-instruction-downloader
```

## Быстрый старт

### 1. Запуск приложения

```bash
# Из командной строки
job-downloader

# Или напрямую через Python
python -m job_instruction_downloader.src.main
```

### 2. Настройка облачного хранилища

1. Откройте настройки приложения
2. Выберите облачный сервис (Google Drive, OneDrive, и т.д.)
3. Следуйте инструкциям для авторизации
4. Настройте структуру папок

### 3. Добавление источника данных

1. Используйте мастер добавления ресурсов
2. Укажите URL и тип ресурса
3. Настройте селекторы элементов
4. Протестируйте конфигурацию

### 4. Запуск загрузки

1. Выберите отделы/категории для загрузки
2. Нажмите кнопку "Старт"
3. Отслеживайте прогресс в реальном времени

## Структура проекта

```
job_instruction_downloader/
├── src/
│   ├── gui/                    # GUI компоненты
│   ├── core/                   # Основная логика
│   │   └── parsers/           # Парсеры сайтов
│   ├── utils/                 # Утилиты
│   └── models/                # Модели данных
├── config/                    # Конфигурационные файлы
│   ├── sites/                 # Конфигурации сайтов
│   └── parsers/               # Конфигурации парсеров
├── logs/                      # Логи приложения
├── downloads/                 # Временные загрузки
└── tests/                     # Тесты
```

## Конфигурация

### Основные настройки

Основные настройки находятся в файле `config/settings.json`:

```json
{
  "application": {
    "name": "Job Instruction Downloader",
    "version": "1.0.0",
    "debug": false,
    "log_level": "INFO"
  },
  "selenium": {
    "browser": "chrome",
    "headless": true,
    "window_size": [1920, 1080]
  },
  "cloud_storage": {
    "default_provider": "google_drive",
    "create_folders_automatically": true
  }
}
```

### Настройка сайтов

Каждый поддерживаемый сайт имеет свой конфигурационный файл в `config/sites/`:

```json
{
  "site_config": {
    "name": "Consultant.ru",
    "base_url": "https://cloud.consultant.ru",
    "document_extraction": {
      "download_button_selector": "[devinid='14']",
      "file_validation": {
        "min_size_bytes": 30000,
        "expected_extensions": [".docx", ".pdf"]
      }
    }
  }
}
```

## Разработка

### Настройка среды разработки

```bash
# Установка зависимостей для разработки
pip install -r requirements.txt

# Установка pre-commit hooks (опционально)
pre-commit install

# Запуск тестов
pytest

# Проверка кода
flake8 job_instruction_downloader
mypy job_instruction_downloader --ignore-missing-imports
```

### Запуск тестов

```bash
# Все тесты
pytest

# Конкретный тест
pytest job_instruction_downloader/tests/test_config.py

# С покрытием кода
pytest --cov=job_instruction_downloader
```

### Создание нового парсера

1. Создайте файл в `src/core/parsers/`
2. Наследуйтесь от `BaseResourceAdapter`
3. Реализуйте необходимые методы
4. Добавьте конфигурацию в `config/sites/`
5. Добавьте тесты

## Этапы разработки

### Фаза 1: Базовая функциональность ✅
- [x] Настройка проекта и структуры
- [x] Базовый GUI
- [x] Основной модуль скачивания
- [x] Простая валидация файлов

### Фаза 2: Интеграция и улучшения (в разработке)
- [ ] Интеграция с Google Drive API
- [ ] Улучшенная обработка ошибок
- [ ] Система логирования
- [ ] Конфигурационные файлы

### Фаза 3: Полировка и тестирование (планируется)
- [ ] Комплексное тестирование
- [ ] Улучшение UI/UX
- [ ] Оптимизация производительности
- [ ] Документация пользователя

### Фаза 4: Развертывание (планируется)
- [ ] Упаковка приложения
- [ ] Создание установщика
- [ ] Финальное тестирование
- [ ] Подготовка релиза

## Лицензия

MIT License. См. файл [LICENSE](LICENSE) для подробностей.

## Поддержка

- **Документация**: [Полный план разработки](plan.md)
- **Issues**: [GitHub Issues](https://github.com/CoreTwin/web2-parser-py/issues)
- **Email**: info@coretwin.com

## Авторы

© 2025 CoreTwin

---

**Примечание**: Проект находится в активной разработке. Некоторые функции могут быть недоступны в текущей версии.
