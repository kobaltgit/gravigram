# Чеклист Проекта (Project Checklist)

В данном файле отслеживается статус готовности всех модулей, функций и интеграций.

---

## 📌 Обозначения
* `[x]` — Реализовано, протестировано и подтверждено
* `[/]` — В процессе тестирования / доработки
* `[ ]` — Запланировано

---

## 🗂 1. База Данных и Конфигурация
- [x] Конфигурация через `.env` и Pydantic Settings ([`src/config.py`](file:///d:/Projects/active/antigravity_bot/src/config.py))
- [x] Асинхронный движок SQLite на `aiosqlite` ([`src/database.py`](file:///d:/Projects/active/antigravity_bot/src/database.py))
- [x] Таблица `projects` (управление воркспейсами и активным проектом)
- [x] Таблица `sessions` (сохранение истории бесед и сессий `agy`)
- [x] Таблица `scheduled_tasks` (расписание автозаданий агента)
- [x] Таблица `settings` (автономия, модель, подтверждения)
- [x] Таблица `models` (каталог моделей Antigravity)

---

## 🤖 2. Ядро Агента Antigravity
- [x] Менеджер агента [`src/agent/manager.py`](file:///d:/Projects/active/antigravity_bot/src/agent/manager.py)
- [x] Прямой запуск `agy.exe` через `stream-json` в headless-режиме
- [x] Автономный режим с флагом `--dangerously-skip-permissions`
- [x] Режим подтверждения опасных действий (`confirm_mode`)
- [x] Форматирование и стриминг мыслей ИИ [`src/agent/executor.py`](file:///d:/Projects/active/antigravity_bot/src/agent/executor.py)
- [x] Контекст Proxmox VE (хост `192.168.1.101`, CT 107, CT 101) для моментального выполнения devops-задач

---

## 📱 3. Telegram-бот (aiogram 3)
- [x] Авторизация администратора через `AuthMiddleware` ([`src/bot/middlewares/auth.py`](file:///d:/Projects/active/antigravity_bot/src/bot/middlewares/auth.py))
- [x] Обработка текстового чата и непрерывный стриминг ([`src/bot/handlers/chat.py`](file:///d:/Projects/active/antigravity_bot/src/bot/handlers/chat.py))
- [x] Локальное распознавание голосовых сообщений (Whisper STT) ([`src/agent/transcriber.py`](file:///d:/Projects/active/antigravity_bot/src/agent/transcriber.py))
- [x] Преобразование Markdown в нативный Telegram HTML ([`src/bot/formatter.py`](file:///d:/Projects/active/antigravity_bot/src/bot/formatter.py))
- [x] Кнопка отмены активной задачи (`/cancel`)
- [x] Меню проектов (`/projects`) и бесед (`/chats`, `/new`)
- [x] Переключение автономного режима (`/mode`, `/auto`, `/confirm`)
- [x] Меню выбора моделей ИИ (`/models`)
- [x] Меню и CLI управления планировщиком (`/tasks`, `/add_task`)
- [x] Двуязычный интерфейс Telegram-бота (RU/EN, команда `/lang`, кнопка `🌐 Язык`) ([`src/i18n.py`](file:///d:/Projects/active/antigravity_bot/src/i18n.py))

---

## 🌐 4. Flutter Web Mini App (TMA)
- [x] FastSPA на Flutter 3.44+ / Dart (`frontend_flutter/`)
- [x] Интеграция с Telegram WebApp SDK (`telegram-web-app.js`, themeParams, haptics)
- [x] Двуязычная система (RU/EN, `LanguageController`, переключатели в AppBar и Settings) ([`frontend_flutter/lib/i18n/`](file:///d:/Projects/active/antigravity_bot/frontend_flutter/lib/i18n/))
- [x] Экран статуса и метрик агента ([`HomeScreen`](file:///d:/Projects/active/antigravity_bot/frontend_flutter/lib/screens/home_screen.dart))
- [x] Экран управления проектами ([`ProjectsScreen`](file:///d:/Projects/active/antigravity_bot/frontend_flutter/lib/screens/projects_screen.dart))
- [x] Экран истории бесед ([`SessionsScreen`](file:///d:/Projects/active/antigravity_bot/frontend_flutter/lib/screens/sessions_screen.dart))
- [x] Экран планировщика заданий ([`TasksScreen`](file:///d:/Projects/active/antigravity_bot/frontend_flutter/lib/screens/tasks_screen.dart))
- [x] Экран системных настроек ([`SettingsScreen`](file:///d:/Projects/active/antigravity_bot/frontend_flutter/lib/screens/settings_screen.dart))
- [x] Криптографическая валидация `initData` (`HMAC-SHA256`) в [`src/server/auth.py`](file:///d:/Projects/active/antigravity_bot/src/server/auth.py)

---

## 🏰 5. Инфраструктура HomeLab & Proxmox
- [x] Выделенный LXC Контейнер **CT 107 (`agy-miniapp`, IP: `192.168.5.128`)**
- [x] Nginx веб-сервер в CT 107 со SPA-роутингом и проксированием `/api/`
- [x] Домен `https://agy.bargcraft.top` с SSL Let's Encrypt в Nginx Proxy Manager (CT 101)
- [x] Мобильный доступ проверен и полностью работоспособен

---

## 🚀 6. Спринт 1: База Универсальности & All-in-One
- [x] Удаление хардкода Proxmox из ядра ([`src/agent/manager.py`](file:///d:/Projects/active/antigravity_bot/src/agent/manager.py)) и динамическое автоопределение ОС
- [x] Кроссплатформенный поиск бинарника `agy` (Linux, Windows, PATH, `AGY_BIN_PATH` в `.env`)
- [x] SPA Fallback в FastAPI ([`src/server/app.py`](file:///d:/Projects/active/antigravity_bot/src/server/app.py)) для автономного хостинга Flutter Web
- [x] Кроссплатформенные скрипты сборки веба `scripts/build_web.sh` и `scripts/build_web.ps1`
- [x] Интерактивный CLI-мастер установки (`setup.py` / `install.sh`) с пошаговым диалогом и автогенерацией `.env`
- [x] Автоматическая настройка домена, Nginx reverse proxy и выпуск SSL Let's Encrypt (Certbot) в мастере установки ([`setup.py`](file:///d:/Projects/active/antigravity_bot/setup.py))

---

## 📦 7. Спринт 2: Упаковка & Мультимодальность Бота
- [x] Автономная установка `agy` через `install.sh`, `install.ps1` и `setup.py`
- [x] Мультистейдж `Dockerfile` и `docker-compose.yml` с монтированием томов
- [x] Готовый шаблон службы `deploy/antigravity-bot.service` для Linux systemd
- [x] Приём входящих файлов и документов (`.log`, `.py`, `.txt`, `.json`, `.csv`, `.pdf`) в Telegram-боте
- [x] Автоматическая отправка созданных артефактов и отчётов документом в Telegram (`send_document`)
- [x] Создание таблицы `task_runs` в SQLite БД и фиксация истории запусков планировщика
- [x] Быстрые интерактивные кнопки (Quick Actions) в клавиатуре Telegram и команда `/quick`

---

## 📱 8. Спринт 3: Flutter Mini App 2.0
- [x] Экран детального просмотра истории сообщений выбранной беседы в TMA ([`SessionsScreen`](file:///d:/Projects/active/antigravity_bot/frontend_flutter/lib/screens/sessions_screen.dart))
- [x] Встроенный проводник файлов и просмотр кода проекта ([`ProjectsScreen`](file:///d:/Projects/active/antigravity_bot/frontend_flutter/lib/screens/projects_screen.dart))
- [x] Модальный просмотр журнала истории выполнений задач в [`TasksScreen`](file:///d:/Projects/active/antigravity_bot/frontend_flutter/lib/screens/tasks_screen.dart)
- [x] Компиляция релизного бандла Flutter Web и обновление архива `miniapp_web.tar.gz`

---

## ⚡ 9. Спринт 4: Управление Планировщиком & Воркспейсами
- [x] Функция `update_scheduled_task` в [`src/database.py`](file:///d:/Projects/active/antigravity_bot/src/database.py) и эндпоинт `PUT /api/tasks/{id}` в [`src/server/app.py`](file:///d:/Projects/active/antigravity_bot/src/server/app.py)
- [x] Кнопка и диалог редактирования задач в [`TasksScreen`](file:///d:/Projects/active/antigravity_bot/frontend_flutter/lib/screens/tasks_screen.dart) с предзаполненными данными
- [x] Нативный диалог выбора времени `TimePicker` в Flutter UI для задач
- [x] Готовые шаблоны задач (аудит, тесты, очистка) в 1 клик
- [x] Безопасное удаление неактивных проектов из базы данных в [`ProjectsScreen`](file:///d:/Projects/active/antigravity_bot/frontend_flutter/lib/screens/projects_screen.dart)
- [x] Релизная компиляция Flutter Web и деплой на сервер `192.168.5.128` (/var/www/html)
- [x] Интерактивная OAuth-авторизация в CLI через [`setup.py`](file:///d:/Projects/active/antigravity_bot/setup.py) (`check_agy_auth` и `interactive_agy_auth`)
- [x] Авторизация Antigravity через Telegram-бота (`/login`): перехват OAuth URL, безопасный ввод ответного ключа через чат и автопроверка статуса ([`src/bot/handlers/auth_login.py`](file:///d:/Projects/active/antigravity_bot/src/bot/handlers/auth_login.py))
- [x] Постоянная кнопка **«🔑 Аккаунты»** на клавиатуре бота и менеджер мульти-аккаунтов с переключением профилей Google в 1 клик ([`src/agent/accounts.py`](file:///d:/Projects/active/antigravity_bot/src/agent/accounts.py))
- [x] Прямой Google OAuth 2.0 flow с loopback-приёмником на порту 8085 и ручным вводом кода/ссылки из адресной строки браузера ([`src/bot/handlers/auth_login.py`](file:///d:/Projects/active/antigravity_bot/src/bot/handlers/auth_login.py))

---

## 🧪 10. Комплексное Автоматизированное Тестирование (70 тестов, 100% Pass)
- [x] Настройка тестового раннера `pytest`, `pytest-asyncio`, `pytest-cov` и конфигурации [`pytest.ini`](file:///d:/Projects/active/antigravity_bot/pytest.ini)
- [x] Изолированное тестовое окружение БД (`isolated_db` fixture в [`tests/conftest.py`](file:///d:/Projects/active/antigravity_bot/tests/conftest.py))
- [x] Модульные тесты конфигурации и настроек ([`tests/test_config.py`](file:///d:/Projects/active/antigravity_bot/tests/test_config.py))
- [x] Полное CRUD тестирование базы данных SQLite ([`tests/test_database.py`](file:///d:/Projects/active/antigravity_bot/tests/test_database.py))
- [x] Тестирование двуязычной системы i18n и 100% паритета словарей ([`tests/test_i18n.py`](file:///d:/Projects/active/antigravity_bot/tests/test_i18n.py))
- [x] Криптографическое тестирование авторизации TMA и HMAC-SHA256 ([`tests/test_tma_auth.py`](file:///d:/Projects/active/antigravity_bot/tests/test_tma_auth.py))
- [x] Сквозное тестирование REST API всех эндпоинтов ([`tests/test_server_api.py`](file:///d:/Projects/active/antigravity_bot/tests/test_server_api.py))
- [x] Тестирование Telegram HTML конвертера ([`tests/test_bot_formatter.py`](file:///d:/Projects/active/antigravity_bot/tests/test_bot_formatter.py))
- [x] Тестирование всех инлайн и reply клавиатур ([`tests/test_bot_keyboards.py`](file:///d:/Projects/active/antigravity_bot/tests/test_bot_keyboards.py))
- [x] Тестирование парсера расписаний и cron ([`tests/test_scheduler.py`](file:///d:/Projects/active/antigravity_bot/tests/test_scheduler.py))
- [x] Тестирование стриминга мыслей и инструментов ([`tests/test_agent_executor.py`](file:///d:/Projects/active/antigravity_bot/tests/test_agent_executor.py))
- [x] Тестирование процессов агента и подтверждений ([`tests/test_agent_manager.py`](file:///d:/Projects/active/antigravity_bot/tests/test_agent_manager.py))
- [x] Тестирование менеджера аккаунтов Google ([`tests/test_accounts.py`](file:///d:/Projects/active/antigravity_bot/tests/test_accounts.py))
- [x] Кроссплатформенный условный импорт для запуска тестов Flutter на Dart VM ([`web_helper.dart`](file:///d:/Projects/active/antigravity_bot/frontend_flutter/lib/services/web_helper.dart))
- [x] Модульные тесты моделей Flutter ([`frontend_flutter/test/models_test.dart`](file:///d:/Projects/active/antigravity_bot/frontend_flutter/test/models_test.dart))
- [x] Модульные тесты локализации Flutter ([`frontend_flutter/test/i18n_test.dart`](file:///d:/Projects/active/antigravity_bot/frontend_flutter/test/i18n_test.dart))
- [x] Виджет-тесты всех экранов Flutter Mini App ([`frontend_flutter/test/screens_test.dart`](file:///d:/Projects/active/antigravity_bot/frontend_flutter/test/screens_test.dart))
- [x] Smoke-тест запуска Flutter Mini App ([`frontend_flutter/test/widget_test.dart`](file:///d:/Projects/active/antigravity_bot/frontend_flutter/test/widget_test.dart))


