# Дорожная Карта (Roadmap): Antigravity Telegram Bot & Flutter Mini App

Данный документ описывает этапы разработки, ключевые вехи, зависимости и актуальное состояние проекта.

---

## 🎯 Общее видение проекта
Создание автономного и удобного моста между экосистемой **Google Antigravity** и пользователем через **Telegram** (нативный чат с живым стримингом мыслей и инструментов, поддержкой голосового ввода через Whisper + **Flutter Web Telegram Mini App** на сервере Proxmox для визуального управления проектами, сессиями и планировщиком).

---

## 📅 Фазы разработки

```mermaid
gantt
    title Дорожная карта разработки
    dateFormat  YYYY-MM-DD
    section Фаза 1: Архитектура и БД
    Проектирование схем данных       :done, p1_1, 2026-08-30, 1d
    Инициализация репозитория и wiki :done, p1_2, 2026-08-30, 1d
    Реализация слоя БД (SQLite)      :done, p1_3, 2026-08-30, 1d
    section Фаза 2: Antigravity Engine
    Интеграция с локальным agy.exe   :done, p2_1, 2026-08-30, 1d
    Менеджер сессий и воркспейсов    :done, p2_2, 2026-08-30, 1d
    Хуки стриминга и подтверждений   :done, p2_3, 2026-08-30, 1d
    section Фаза 3: Telegram Bot
    Каркас aiogram 3 и Middleware    :done, p3_1, 2026-08-30, 1d
    Обработка чата со стримингом     :done, p3_2, 2026-08-30, 1d
    Локальное распознавание (Whisper):done, p3_3, 2026-08-30, 1d
    Команды и Inline-меню            :done, p3_4, 2026-08-30, 1d
    section Фаза 4: Flutter Mini App
    FastAPI сервер и REST эндпоинты  :done, p4_1, 2026-08-30, 1d
    Flutter Web TMA Приложение       :done, p4_2, 2026-08-30, 1d
    Криптографическая защита TMA Auth:done, p4_3, 2026-08-30, 1d
    section Фаза 5: Развертывание Proxmox
    LXC Контейнер CT 107 (Nginx)     :done, p5_1, 2026-08-30, 1d
    Nginx Proxy Manager & SSL HTTPS  :done, p5_2, 2026-08-30, 1d
    Доверенная подсеть HomeLab       :done, p5_3, 2026-08-30, 1d
    section Фаза 6: Планировщик Задач
    AgentScheduler (Cron / HH:MM)    :done, p6_1, 2026-08-30, 1d
    Экран TasksScreen в Mini App     :done, p6_2, 2026-08-30, 1d
    Автономный аудит Proxmox и дисков:done, p6_3, 2026-08-30, 1d
    section Спринт 1: База Универсальности
    Очистка ядра от Proxmox          :done, p7_1, 2026-10-07, 1d
    Кроссплатформенный поиск agy     :done, p7_2, 2026-10-07, 1d
    SPA Fallback в FastAPI           :done, p7_3, 2026-10-07, 1d
    Интерактивный Setup Wizard       :done, p7_4, 2026-10-07, 1d
    section Спринт 2: Упаковка & Бот
    Docker & Systemd упаковка        :done, p8_1, 2026-10-07, 1d
    Прием документов (.log, .py)     :done, p8_2, 2026-10-07, 1d
    Авто-доставка артефактов в TG    :done, p8_3, 2026-10-07, 1d
    Таблица task_runs и логи         :done, p8_4, 2026-10-07, 1d
    section Спринт 3: Mini App 2.0
    История сообщений сессии в TMA   :done, p9_1, 2026-10-07, 1d
    Файловый браузер проектов в TMA  :done, p9_2, 2026-10-07, 1d
    Журнал истории задач в UI        :done, p9_3, 2026-10-07, 1d
    section Спринт 4: Планировщик & Воркспейсы
    Редактирование задач (PUT API)   :done, p10_1, 2026-10-07, 1d
    TimePicker и шаблоны задач в UI  :done, p10_2, 2026-10-07, 1d
    Удаление и переключение проектов :done, p10_3, 2026-10-07, 1d
    Деплой обновлений на сервер      :done, p10_4, 2026-10-07, 1d
    section Спринт 5: Ребрендинг & i18n
    Gravigram брендинг и векторное лого:done, p11_1, 2026-10-07, 1d
    Двуязычный бот и Mini App (RU/EN) :done, p11_2, 2026-10-07, 1d
    section Спринт 6: Тестирование (100% Pass)
    Pytest бэкенд с изоляцией SQLite :done, p12_1, 2026-10-07, 1d
    Flutter UI & Model тесты         :done, p12_2, 2026-10-07, 1d
    Кроссплатформенный test runner   :done, p12_3, 2026-10-07, 1d
```

---

## 📌 Детализация этапов

### Фаза 1: Фундамент и База Данных (Статус: ✅ Завершено)
- [x] Определение архитектурных требований и согласование дизайна с пользователем (Flutter Web для TMA).
- [x] Формирование структуры каталога `wiki/` и проектных правил агента.
- [x] Разработка модуля [`src/config.py`](file:///d:/Projects/active/antigravity_bot/src/config.py) для валидации `.env`.
- [x] Создание асинхронного слоя БД [`src/database.py`](file:///d:/Projects/active/antigravity_bot/src/database.py) на `aiosqlite` (таблицы `projects`, `sessions`, `settings`, `models`, `scheduled_tasks`).
- [x] Написание и успешное выполнение модульных тестов БД.

### Фаза 2: Antigravity Agent Core (Статус: ✅ Завершено)
- [x] Создание модуля [`src/agent/manager.py`](file:///d:/Projects/active/antigravity_bot/src/agent/manager.py) с прямым запуском `agy.exe` через `stream-json`.
- [x] Реализация флага `--dangerously-skip-permissions` для автономного выполнения инструментов на ПК.
- [x] Создание модуля [`src/agent/executor.py`](file:///d:/Projects/active/antigravity_bot/src/agent/executor.py) с троттлингом стриминга и безопасным выводом мыслей/инструментов.
- [x] Внедрение контекста инфраструктуры (Proxmox, CT 107, CT 101, локальный ПК) для моментального выполнения системных задач.

### Фаза 3: Telegram Bot & Мультимодальность (Статус: ✅ Завершено)
- [x] Каркас бота на `aiogram 3` с проверкой прав администратора (`AuthMiddleware`).
- [x] Команды: `/start`, `/help`, `/new`, `/projects`, `/chats`, `/mode`, `/status`, `/tasks`, `/add_task`, `/cancel`.
- [x] Локальная транскрипция голосовых сообщений на нейросети `faster-whisper` (без API-ключей и облака).
- [x] Чистый текстовый вывод с живым стримингом мыслей и инструментов.
- [x] Безопасная обработка сущностей Telegram (`safe_edit`, `safe_send`) с автоматическим fallback на обычный текст при синтаксических сбоях.

### Фаза 4: Flutter Mini App & FastAPI Сервер (Статус: ✅ Завершено)
- [x] REST API на FastAPI [`src/server/app.py`](file:///d:/Projects/active/antigravity_bot/src/server/app.py).
- [x] Экран проектов [`ProjectsScreen`](file:///d:/Projects/active/antigravity_bot/frontend_flutter/lib/screens/projects_screen.dart).
- [x] Экран бесед [`SessionsScreen`](file:///d:/Projects/active/antigravity_bot/frontend_flutter/lib/screens/sessions_screen.dart).
- [x] Экран плановых заданий [`TasksScreen`](file:///d:/Projects/active/antigravity_bot/frontend_flutter/lib/screens/tasks_screen.dart).
- [x] Экран настроек [`SettingsScreen`](file:///d:/Projects/active/antigravity_bot/frontend_flutter/lib/screens/settings_screen.dart).
- [x] Криптографическая валидация `initData` Telegram WebApp (`HMAC-SHA256`).

### Фаза 5: Первичное Развертывание в HomeLab (Статус: ✅ Завершено)
- [x] Создание отдельного LXC-контейнера **CT 107 (`agy-miniapp`)** на хосте Proxmox VE (`192.168.1.101`).
- [x] Настройка Nginx в CT 107 (SPA-роутинг, сжатие gzip, отключение кэша для JS/HTML, проксирование `/api/` на `192.168.5.107:8000`).
- [x] Настройка Nginx Proxy Manager на CT 101 и выпуск SSL-сертификата Let's Encrypt для домена `https://agy.bargcraft.top`.

### Фаза 6: Фоновый Планировщик Автономных Заданий (Статус: ✅ Завершено)
- [x] Реализация модуля [`src/agent/scheduler.py`](file:///d:/Projects/active/antigravity_bot/src/agent/scheduler.py) с поддержкой времени `HH:MM` и `cron`.
- [x] Автономный запуск ИИ-агента Antigravity по расписанию и доставка отчетов в Telegram.
- [x] Интеграция CLI-утилиты [`src/agent/schedule_cli.py`](file:///d:/Projects/active/antigravity_bot/src/agent/schedule_cli.py) для естественного создания задач в чате.

### Спринт 1: База Платформонезависимости & All-in-One (Статус: ✅ Завершено)
- [x] Удаление хардкода Proxmox из ядра (`src/agent/manager.py`) и автоопределение ОС.
- [x] Кроссплатформенный поиск бинарника `agy` (Linux, Windows, PATH, `AGY_BIN_PATH`).
- [x] SPA Fallback в FastAPI (`src/server/app.py`) для автономного хостинга Mini App без внешнего веб-сервера.
- [x] Кроссплатформенные скрипты сборки `scripts/build_web.sh` и `scripts/build_web.ps1`.
- [x] Интерактивный CLI-мастер установки (`setup.py`, `install.sh`, `install.ps1`) с пошаговым диалогом настройки.

### Спринт 2: Упаковка & Мультимодальность Бота (Статус: ✅ Завершено)
- [x] Автономная установка `agy` через `install.sh`, `install.ps1` и `setup.py`.
- [x] Docker & Docker Compose (`Dockerfile`, `docker-compose.yml`) и шаблон службы `systemd`.
- [x] Приём входящих файлов и документов (`.log`, `.py`, `.txt`, `.json`, `.csv`, `.pdf`) в боте.
- [x] Автоматическая отправка созданных артефактов документом в Telegram (`send_document`).
- [x] Таблица `task_runs` в SQLite и детальная фиксация истории запусков планировщика.
- [x] Быстрые действия (Quick Actions) и кнопка «⚡ Действия» в клавиатуре бота.

### Спринт 3: Flutter Mini App 2.0 (Статус: ✅ Завершено)
- [x] Экран просмотра истории сообщений беседы в TMA ([`SessionsScreen`](file:///d:/Projects/active/antigravity_bot/frontend_flutter/lib/screens/sessions_screen.dart)).
- [x] Встроенный файловый браузер проектов (File Explorer & Monospace Code Viewer) в TMA ([`ProjectsScreen`](file:///d:/Projects/active/antigravity_bot/frontend_flutter/lib/screens/projects_screen.dart)).
- [x] Вкладка и модальное окно истории выполнения заданий в экране [`TasksScreen`](file:///d:/Projects/active/antigravity_bot/frontend_flutter/lib/screens/tasks_screen.dart) с просмотром отчётов.
- [x] Сборка релизного бандла Flutter Web и обновление архива `miniapp_web.tar.gz`.

### Спринт 4: Управление Планировщиком & Воркспейсами (Статус: ✅ Завершено)
- [x] Реализована функция `update_scheduled_task` в [`src/database.py`](file:///d:/Projects/active/antigravity_bot/src/database.py) и эндпоинт `PUT /api/tasks/{id}` в [`src/server/app.py`](file:///d:/Projects/active/antigravity_bot/src/server/app.py).
- [x] В [`TasksScreen`](file:///d:/Projects/active/antigravity_bot/frontend_flutter/lib/screens/tasks_screen.dart) добавлена кнопка редактирования задач с предзаполненными полями, визуальный диалог выбора времени `TimePicker` и быстрые шаблоны автозаданий (аудит, тесты, очистка кэша).
- [x] В [`ProjectsScreen`](file:///d:/Projects/active/antigravity_bot/frontend_flutter/lib/screens/projects_screen.dart) добавлено безопасное удаление неактивных проектов из БД с диалогом подтверждения.
- [x] Скомпилирован релиз Flutter Web (`flutter build web --release`), обновлён архив `miniapp_web.tar.gz` и развёрнут на боевом сервере `192.168.5.128` (/var/www/html).

### Спринт 5: Ребрендинг Gravigram & Двуязычность (Статус: ✅ Завершено)
- [x] Ребрендинг проекта в **Gravigram** во всей кодовой базе, скриптах развертывания, systemd и документации.
- [x] Оптимизация и интеграция SVG-логотипа в README и Mini App.
- [x] Полная двуязычная локализация (RU/EN) Telegram-бота и Flutter Mini App с мгновенным переключением языка.

### Спринт 6: Комплексное Автоматизированное Тестирование (Статус: ✅ Завершено)
- [x] Модульное и интеграционное тестирование Python-бэкенда (59 тестов, 100% Pass, изоляция SQLite, валидация TMA HMAC-SHA256).
- [x] Модульное и компонентное тестирование Flutter Mini App (11 тестов, 100% Pass, кроссплатформенный запуск без привязки к `dart:js`).
- [x] Создание единых скриптов запуска тестового набора: `scripts/run_tests.ps1` (Windows) и `scripts/run_tests.sh` (Linux/macOS).


