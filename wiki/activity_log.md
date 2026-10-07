# Журнал Выполненных Действий (Activity Log)

В данном файле хронологически фиксируются все выполненные изменения, архитектурные решения, создание компонентов и обновления структуры проекта.

---

## Формат записей
Каждая запись содержит дату, инициатора (пользователь / агент), категорию и подробное описание изменений со ссылками на затронутые файлы.

---

## 📜 Хронология

### 2026-10-07
* **Двуязычный мастер установки (EN / RU, английский по умолчанию с переключателем)**:
  * В [`setup.py`](file:///d:/Projects/active/antigravity_bot/setup.py) внедрена полноценная интернационализация: поддержка аргумента `--lang {en,ru}` и интерактивный селектор при запуске с английским языком по умолчанию (`[1] English (default)`, `[2] Русский`). Все баннеры, шаги, валидаторы, ошибки и подсказки переведены на два языка. Выбранный язык автоматически прописывается в `.env` (`DEFAULT_LANGUAGE`) и в базу данных `data/bot.db` (`settings.language`).
  * В [`install.sh`](file:///d:/Projects/active/antigravity_bot/install.sh) добавлен стартовый селектор языка, поддержка аргумента `--lang`, двуязычные системные логи и передача выбранного языка в `setup.py`.
  * В [`install.ps1`](file:///d:/Projects/active/antigravity_bot/install.ps1) добавлен параметр `-Language`, интерактивный выбор языка для Windows PowerShell и передача в `setup.py`.
  * Разработан модульный набор тестов [`tests/test_setup_wizard.py`](file:///d:/Projects/active/antigravity_bot/tests/test_setup_wizard.py) (5 тестов: валидаторы, выбор языка, интерактивный режим, функция `t`). Общее число тестов проекта выросло до 75 (64 backend + 11 frontend, 100% pass rate).
  * Обновлены бейджи и описания тестов в [`README.md`](file:///d:/Projects/active/antigravity_bot/README.md) и [`README_RU.md`](file:///d:/Projects/active/antigravity_bot/README_RU.md).


* **Исправление распаковки и маршрутизации Flutter Web Mini App (BUG-033)**:
  * В [`setup.py`](file:///d:/Projects/active/antigravity_bot/setup.py) добавлена проверка внутренней структуры `miniapp_web.tar.gz` и автоматический перенос файлов из `frontend_flutter/build/` в `build/web/`.
  * В [`install.sh`](file:///d:/Projects/active/antigravity_bot/install.sh) и [`install.ps1`](file:///d:/Projects/active/antigravity_bot/install.ps1) исправлены пути распаковки архива и закрыта скобка условия.
  * В [`src/server/app.py`](file:///d:/Projects/active/antigravity_bot/src/server/app.py) внедрён автоматический fallback `WEB_DIR`: если `index.html` отсутствует в `build/web/`, но найден в `build/`, сервер обслуживает его без сбоев.

* **Смена лицензии проекта с MIT на GNU AGPLv3**:
  * Создан [`LICENSE`](file:///d:/Projects/active/antigravity_bot/LICENSE) — официальный текст GNU Affero General Public License v3.0 (скачан с gnu.org).
  * Обновлён бейдж лицензии и секция `## 📄 License` в [`README.md`](file:///d:/Projects/active/antigravity_bot/README.md).
  * Обновлён бейдж лицензии и секция `## 📄 Лицензия` в [`README_RU.md`](file:///d:/Projects/active/antigravity_bot/README_RU.md).
* **Устранение блокировки GitHub Push Protection и вынос секретов OAuth**:
  * В [`src/agent/accounts.py`](file:///d:/Projects/active/antigravity_bot/src/agent/accounts.py) устранены захардкоженные `GOOGLE_CLIENT_ID` и `GOOGLE_CLIENT_SECRET`. Добавлены функции безопасного динамического чтения `get_google_client_id()` и `get_google_client_secret()` из переменных окружения и настроек.
  * В [`src/config.py`](file:///d:/Projects/active/antigravity_bot/src/config.py) добавлены поля `google_client_id` и `google_client_secret`.
  * В [`.env.example`](file:///d:/Projects/active/antigravity_bot/.env.example) добавлены плейсхолдеры для Google OAuth настроек.
  * В локальный [`.env`](file:///d:/Projects/active/antigravity_bot/.env) сохранены рабочие ключи без риска утечки в репозиторий.
  * В [`.gitignore`](file:///d:/Projects/active/antigravity_bot/.gitignore) добавлен `.coverage` и `.coverage.*`, файл `.coverage` убран из индекса Git.
  * Успешно верифицировано прохождение тестов (59/59 pass).

* **Полное покрытие проекта автоматизированными тестами (Backend + Frontend, 70 тестов)**:
  * **Python Backend (`pytest` + `pytest-asyncio` + `pytest-cov`, 59 тестов)**:
    * Создан [`pytest.ini`](file:///d:/Projects/active/antigravity_bot/pytest.ini) с автоматической изоляцией сред, поддержкой asyncio и маркером `integration`.
    * Создан [`tests/conftest.py`](file:///d:/Projects/active/antigravity_bot/tests/conftest.py) с фикстурами временной изолированной SQLite БД (`isolated_db`), генератором криптографических подписей Telegram `initData` и клиентами `TestClient`.
    * Разработаны модульные и интеграционные тесты:
      * [`tests/test_config.py`](file:///d:/Projects/active/antigravity_bot/tests/test_config.py): валидация конфигурации, путей и переменных окружения Pydantic Settings.
      * [`tests/test_database.py`](file:///d:/Projects/active/antigravity_bot/tests/test_database.py): полное CRUD-тестирование проектов, сессий, задач, настроек, моделей и языка.
      * [`tests/test_i18n.py`](file:///d:/Projects/active/antigravity_bot/tests/test_i18n.py): 100% паритет ключей словарей RU/EN, интерполяция аргументов, fallback и выбор локали.
      * [`tests/test_tma_auth.py`](file:///d:/Projects/active/antigravity_bot/tests/test_tma_auth.py): проверка HMAC-SHA256 подписи Telegram WebApp, защита от replay-атак (auth_date), блокировка поддельных ID, fail-closed безопасность.
      * [`tests/test_server_api.py`](file:///d:/Projects/active/antigravity_bot/tests/test_server_api.py): сквозные тесты REST API (`/status`, `/projects`, `/sessions`, `/tasks`, `/settings`, `/models`, статический хостинг Flutter Web).
      * [`tests/test_bot_formatter.py`](file:///d:/Projects/active/antigravity_bot/tests/test_bot_formatter.py): конвертация Markdown в Telegram HTML (заголовки, код, списки, ссылки, экранирование HTML).
      * [`tests/test_bot_keyboards.py`](file:///d:/Projects/active/antigravity_bot/tests/test_bot_keyboards.py): построение инлайн и reply-клавиатур на русском и английском.
      * [`tests/test_scheduler.py`](file:///d:/Projects/active/antigravity_bot/tests/test_scheduler.py): парсинг cron и человекопонятного формата времени (`HH:MM`), расчёт следующего запуска.
      * [`tests/test_agent_executor.py`](file:///d:/Projects/active/antigravity_bot/tests/test_agent_executor.py): стриминг мыслей, форматирование инструментов и троттлинг сообщений.
      * [`tests/test_agent_manager.py`](file:///d:/Projects/active/antigravity_bot/tests/test_agent_manager.py): управление процессом агента, отмена задач, резолв подтверждений (`resolve_confirmation`).
      * [`tests/test_accounts.py`](file:///d:/Projects/active/antigravity_bot/tests/test_accounts.py): извлечение JWT email, генерация Google OAuth ссылок, переключение и удаление аккаунтов.
  * **Flutter Frontend (`flutter test`, 11 тестов)**:
    * Устранена платформенная несовместимость `dart:js` на Dart VM: создана модульная архитектура условного импорта (`web_helper_stub.dart`, `web_helper_web.dart`, `web_helper.dart`).
    * [`frontend_flutter/test/models_test.dart`](file:///d:/Projects/active/antigravity_bot/frontend_flutter/test/models_test.dart): тестирование сериализации и десериализации моделей `Project`, `Session`, `ScheduledTask`.
    * [`frontend_flutter/test/i18n_test.dart`](file:///d:/Projects/active/antigravity_bot/frontend_flutter/test/i18n_test.dart): реактивный контроллер `LanguageController`, словарь строк `S.tr`.
    * [`frontend_flutter/test/screens_test.dart`](file:///d:/Projects/active/antigravity_bot/frontend_flutter/test/screens_test.dart): виджет-тестирование экранов `HomeScreen`, `SettingsScreen`, `ProjectsScreen`, `TasksScreen` с `MockApiService`.
    * [`frontend_flutter/test/widget_test.dart`](file:///d:/Projects/active/antigravity_bot/frontend_flutter/test/widget_test.dart): smoke-тест запуска приложения `GravigramMiniApp`.
  * **Единые скрипты автоматического запуска тестов**:
    * Созданы [`scripts/run_tests.ps1`](file:///d:/Projects/active/antigravity_bot/scripts/run_tests.ps1) (Windows PowerShell) и [`scripts/run_tests.sh`](file:///d:/Projects/active/antigravity_bot/scripts/run_tests.sh) (Linux/macOS Bash) для параллельного сквозного прогона всего тестового набора (Python 59 тестов + Flutter 11 тестов = 70 тестов, 100% Pass) в 1 команду.
    * В [`README.md`](file:///d:/Projects/active/antigravity_bot/README.md) и [`README_RU.md`](file:///d:/Projects/active/antigravity_bot/README_RU.md) добавлен официальный бейдж `Tests: 70 passed` со ссылкой на новый раздел документации по автоматизированному тестированию.

  * Обнаружено, что Telegram WebView удерживал в кэше старый `main.dart.js` через Service Worker (`flutter_service_worker.js`).
  * В [`index.html`](file:///d:/Projects/active/antigravity_bot/frontend_flutter/web/index.html) внедрён принудительный скрипт деактивации (`unregister`) всех устаревших Service Workers и очистки хранилища `caches`.
  * В [`flutter_bootstrap.js`](file:///d:/Projects/active/antigravity_bot/frontend_flutter/build/web/flutter_bootstrap.js) отключена регистрация serviceWorker, а `flutter_service_worker.js` заменён скриптом самоликвидации и форсированного обновления.
  * Свежий релиз скомпилирован в `frontend_flutter/build/web/`, перепакован в `miniapp_web.tar.gz` и развернут на сервере `192.168.5.128` (`/var/www/html`).
  * Nginx перезагружен, проверка отдачи `https://agy.bargcraft.top` подтвердила актуальную версию с новым брендингом Gravigram.

* **Двуязычная локализация (Bilingual EN/RU System) в Telegram-боте и Flutter Mini App**:
  * **Бэкенд и Telegram-бот ([`src/i18n.py`](file:///d:/Projects/active/antigravity_bot/src/i18n.py), [`src/bot/commands.py`](file:///d:/Projects/active/antigravity_bot/src/bot/commands.py), [`src/bot/keyboards.py`](file:///d:/Projects/active/antigravity_bot/src/bot/keyboards.py), [`src/bot/handlers/`](file:///d:/Projects/active/antigravity_bot/src/bot/handlers/))**:
    * Создан модуль интернационализации `src/i18n.py` с полной базой переводов на русском и английском языках.
    * Добавлена настройка `language` в таблицу `settings` SQLite БД с методами `get_language()` и `set_language()` в [`src/database.py`](file:///d:/Projects/active/antigravity_bot/src/database.py).
    * Внедрена команда `/lang` / `/language` и кнопка `🌐 Язык (RU/EN)` для мгновенного переключения языка через инлайн-клавиатуру с автоматическим обновлением главного меню.
    * Все экраны (старт, помощь, проекты, сессии, планировщик задач, выбор моделей, статус, подтверждения) поддерживают динамическую локализацию.
  * **Flutter Web Mini App (`frontend_flutter/`)**:
    * Создан `LanguageController` на базе `ChangeNotifier` и словарь строк `S.tr(...)` в [`frontend_flutter/lib/i18n/`](file:///d:/Projects/active/antigravity_bot/frontend_flutter/lib/i18n/).
    * Корневой `MaterialApp` обёрнут в `ListenableBuilder` для реактивной смены языка во всех вкладках без перезагрузки страницы.
    * Добавлен переключатель языка (кнопка `RU`/`EN` в шапке `HomeScreen` и радиокнопки в `SettingsScreen`) с двухсторонней синхронизацией через `/api/settings`.
    * Экраны `HomeScreen`, `ProjectsScreen`, `SessionsScreen`, `TasksScreen`, `SettingsScreen` полностью адаптированы под мультиязычность.

* **Переименование службы systemd на gravigram.service ([`deploy/gravigram.service`](file:///d:/Projects/active/antigravity_bot/deploy/gravigram.service), [`install.sh`](file:///d:/Projects/active/antigravity_bot/install.sh))**:
  * Служба переименована с `antigravity-bot.service` на `gravigram.service`.
  * В `install.sh` добавлена автогенерация службы с подстановкой фактического рабочего каталога (`WorkingDirectory=$SCRIPT_DIR`) и текущего непривилегированного пользователя (`User=$(whoami)`).
  * Обновлены ссылки в документации `README.md` и `README_RU.md`.

* **Оптимизация SVG-логотипа & интеграция в README ([`icon.svg`](file:///d:/Projects/active/antigravity_bot/icon.svg), [`README.md`](file:///d:/Projects/active/antigravity_bot/README.md), [`README_RU.md`](file:///d:/Projects/active/antigravity_bot/README_RU.md))**:
  * Исходный SVG-файл очищен от служебного мусора Adobe Illustrator (удалены избыточные теги заголовков, метаданные экспорта, неиспользуемые стили `st6..st18`, дублирующие слои кругов).
  * Выделен компактный блок `<defs>` с осмысленными градиентами, размер файла уменьшен более чем в 2 раза без потери качества и геометрии.
  * Логотип размещён по центру в заголовках англоязычного и русскоязычного файлов документации (`README.md` и `README_RU.md`).

* **Официальное брендирование проекта — Gravigram & привязка репозитория**:
  * Проведено исследование уникальности названий в экосистеме GitHub. Имя **Gravigram** признано на 100% уникальным и утверждено в качестве официального бренда проекта.
  * Все ссылки и инструкции переведены на официальный репозиторий `https://github.com/kobaltgit/gravigram.git`.
  * Документация ([`README.md`](file:///d:/Projects/active/antigravity_bot/README.md), [`README_RU.md`](file:///d:/Projects/active/antigravity_bot/README_RU.md)) и скрипты установки ([`install.sh`](file:///d:/Projects/active/antigravity_bot/install.sh), [`install.ps1`](file:///d:/Projects/active/antigravity_bot/install.ps1)) полностью обновлены с брендингом Gravigram.

* **Автоматическое клонирование репозитория при установке под ключ ([`install.sh`](file:///d:/Projects/active/antigravity_bot/install.sh), [`install.ps1`](file:///d:/Projects/active/antigravity_bot/install.ps1))**:
  * В скрипты `install.sh` и `install.ps1` добавлена проверка наличия проекта и автоматическое клонирование `git clone <REPO_URL>` при запуске на чистом сервере/ПК вне каталога репозитория.
  * Реализована поддержка как прямого однострочника через `curl ... | bash -s -- <REPO_URL>`, так и интерактивного ввода URL при его отсутствии.
  * Если `git` отсутствует на сервере, скрипт автоматически устанавливает системный пакет `git` через системный менеджер пакетов (`apt`, `dnf`, `pacman`, `winget`).

* **Комплексная документация репозитория & Конфигурация Git**:
  * **Основной README на английском ([`README.md`](file:///d:/Projects/active/antigravity_bot/README.md))**:
    * Подготовлено подробнейшее руководство: архитектура, установка в 1 команду (Linux / Windows / Docker), Multi-Account Manager с Google OAuth 2.0, справочник команд бота, обзор экранов Flutter Mini App, CLI планировщика, таблица всех параметров `.env`.
  * **Русскоязычная документация ([`README_RU.md`](file:///d:/Projects/active/antigravity_bot/README_RU.md))**:
    * Создана синхронизированная русская версия документации аналогичной глубины проработки со ссылками на исходный код и архитектурными диаграммами.
  * **Конфигурация Git ([`.gitignore`](file:///d:/Projects/active/antigravity_bot/.gitignore), [`data/.gitkeep`](file:///d:/Projects/active/antigravity_bot/data/.gitkeep))**:
    * Создан исчерпывающий `.gitignore`, исключающий виртуальные окружения (`venv/`), секреты (`.env*`), SQLite БД (`data/*.db`), сессии, логи (`*.log`), сборки Flutter Web (`build/`, `.dart_tool/`), системные кэши и артефакты ОС.

* **Исправление авторизации и прямой Google OAuth 2.0 протокол (BUG-029)**:
  * **Исправление сбоя при нажатии «Войти в новый аккаунт»**:
    * Устранён `AttributeError: 'AgentSessionManager' object has no attribute 'find_agy'` — добавлен метод `find_agy()` в [`src/agent/manager.py`](file:///d:/Projects/active/antigravity_bot/src/agent/manager.py).
  * **Прямой протокол Google OAuth 2.0 ([`src/agent/accounts.py`](file:///d:/Projects/active/antigravity_bot/src/agent/accounts.py), [`src/bot/handlers/auth_login.py`](file:///d:/Projects/active/antigravity_bot/src/bot/handlers/auth_login.py))**:
    * Внедрена прямая генерация OAuth URL через официальный Client ID / Secret Antigravity (`generate_google_auth_url`), что исключило зависания CLI и конфликты с существующими профилями.
    * Добавлен автоматический локальный приёмник обратного вызова (loopback server) на `127.0.0.1:8085` (`ensure_auth_callback_server`), автоматически завершающий вход при открытии ссылки на том же компьютере.
    * Для мобильных устройств и удалённых серверов обеспечен надёжный fallback: пользователь может отправить в чат выданный код авторизации или адрес из адресной строки браузера (`code=...`). Токены обмениваются и записываются в хранилище без сбоев.
    * Добавлена кнопка «🌐 Войти через Google» (URL-кнопка) и инлайн-кнопка «❌ Отмена» (`acc_cancel_login`).

* **Мульти-аккаунтный менеджер Google Antigravity & Кнопка в меню**:
  * **Хранилище профилей ([`src/agent/accounts.py`](file:///d:/Projects/active/antigravity_bot/src/agent/accounts.py))**:
    * Создан менеджер аккаунтов с безопасным хранилищем токенов `~/.gemini/accounts_vault/`.
    * Реализованы функции автоматического извлечения email из `id_token`, сохранения профилей, переключения активного аккаунта `switch_account` (подмена `oauth_creds.json` и обновление `google_accounts.json` в 1 клик) и удаления отвязанных аккаунтов `remove_account`.
  * **Интерфейс в боте**:
    * В постоянную главную клавиатуру ([`src/bot/keyboards.py`](file:///d:/Projects/active/antigravity_bot/src/bot/keyboards.py)) добавлена кнопка **«🔑 Аккаунты»**.
    * В [`src/bot/handlers/auth_login.py`](file:///d:/Projects/active/antigravity_bot/src/bot/handlers/auth_login.py) реализовано интерактивное меню:
      * Отображение текущего активного профиля Google.
      * Инлайн-кнопки быстрого переключения между всеми сохранёнными аккаунтами без повторного ввода кодов.
      * Кнопка `➕ Войти в новый аккаунт` (запуск Device OAuth с выдачей ссылки и приёмом токена в чате).
      * Меню удаления неактивных аккаунтов `🗑 Удалить...`.
  * **Безопасность (Single-User)**:
    * Подтверждена строгая фильтрация в [`src/bot/middlewares.py`](file:///d:/Projects/active/antigravity_bot/src/bot/middlewares.py): доступ к любым сообщениям, командам, файлам и авторизации закрыт для всех, кроме владельца (`TELEGRAM_ADMIN_ID`).

* **Реализация Авторизации Google Antigravity (в установщике и через Telegram-бота)**:
  * **Авторизация в Мастере установки ([`setup.py`](file:///d:/Projects/active/antigravity_bot/setup.py))**:
    * Добавлены функции `check_agy_auth` (проверка готовности через вызов доступных моделей `agy models`) и `interactive_agy_auth`.
    * Если CLI установлен, но ещё не привязан к Google аккаунту, установщик выводит баннер с инструкцией, запускает интерактивный сеанс, ожидает ввода ответного ключа в терминале и подтверждает успешный вход.
  * **Авторизация в Telegram-боте ([`src/bot/handlers/auth_login.py`](file:///d:/Projects/active/antigravity_bot/src/bot/handlers/auth_login.py))**:
    * Реализована команда `/login` и инлайн-кнопка повторного входа.
    * При вызове бот проверяет статус. Если вход не выполнен (или запрошена смена аккаунта) — бот запускает процесс `agy`, перехватывает сгенерированный OAuth Device URL и отправляет пользователю кликабельную ссылку с инструкцией.
    * Фильтр `IsWaitingAuthCode` перехватывает присланный в чат ответный ключ/токен и передаёт его в `stdin` процесса Antigravity.
    * После валидации токена бот сообщает об успешном завершении авторизации и готовности к диалогу.
    * Добавлена команда отмены `/cancel_login`.
    * Команда `/login` зарегистрирована в `/help`.

* **Спринт 4: Управление Планировщиком & Воркспейсами**:
  * **Редактирование задач (Backend & Frontend)**:
    * В [`src/database.py`](file:///d:/Projects/active/antigravity_bot/src/database.py) добавлена функция `update_scheduled_task` для сохранения изменений (название, расписание, промпт, проект, пересчёт `next_run_at`).
    * В [`src/server/app.py`](file:///d:/Projects/active/antigravity_bot/src/server/app.py) добавлен эндпоинт `PUT /api/tasks/{task_id}` со схемой `UpdateTaskRequest`.
    * В [`ApiService`](file:///d:/Projects/active/antigravity_bot/frontend_flutter/lib/services/api_service.dart) добавлен метод `updateTask`.
    * В [`TasksScreen`](file:///d:/Projects/active/antigravity_bot/frontend_flutter/lib/screens/tasks_screen.dart) на карточки добавлена кнопка редактирования (`Icons.edit_outlined`) и модальное окно `_showEditTaskDialog`.
  * **TimePicker & Быстрые Шаблоны в UI**:
    * В форму добавления/редактирования задач встроен нативный `TimePicker` (`_pickTimeForController`) — выбор времени по клику на часы.
    * Добавлены чипы быстрых пресетов в 1 клик: 🌅 «Утренний аудит системы» (09:00), 🧪 «Запуск тестов и сборки» (12:00), 🧹 «Очистка логов и кэша» (23:00).
  * **Управление проектами и воркспейсами**:
    * В [`ProjectsScreen`](file:///d:/Projects/active/antigravity_bot/frontend_flutter/lib/screens/projects_screen.dart) для неактивных проектов добавлена кнопка удаления (`Icons.delete_outline`) с модальным окном подтверждения.
  * **Сборка и деплой на сервер**:
    * Успешно собран релиз Flutter Web (`flutter build web --release`).
    * Обновлён автономный дистрибутив `miniapp_web.tar.gz`.
    * Через Shellit MCP бандл распакован на боевом сервере `192.168.5.128` (`/var/www/html`), права выставлены для `www-data`, Nginx перезагружен.
    * Тестовые вызовы `PUT /api/tasks/2`, `GET /api/tasks` и `GET /api/projects` подтвердили HTTP 200 OK.

* **Тестирование приёма документов и исправление кодировки логов на Windows (BUG-028)**:
  * **Тест приёма документов**: Пользователь отправил боту `.docx` документ `Types_of_sexual_transference_and_countertransference_in_psychotherapeutic.docx`. Файл сохранён в `.agy_uploads/`, агент Antigravity успешно прочитал документ, составил подробный анализ («Паспорт документа», структуру, ключевые тезисы) и доставил ответ пользователю в Telegram.
  * **Ошибка в консоли Windows**: При выводе эмодзи (`👤`, `🤖`) в логах стандартного вывода `sys.stdout` выбрасывался `UnicodeEncodeError: 'charmap' codec can't encode character` из-за кодировки `cp1251`.
  * **Исправление**: В [`run.py`](file:///d:/Projects/active/antigravity_bot/run.py) добавлена явная переконфигурация потоков `sys.stdout` и `sys.stderr` на `encoding='utf-8'` и добавлен `logging.FileHandler("bot.log", encoding="utf-8")`.
  * **Статус**: Сервер перезапущен и работает стабильно.

* **Устранение ошибки 403 Forbidden и стабилизация соединения (BUG-026, BUG-027)**:
  * **Причина 403**: Бэкенд на `192.168.5.107:8000` блокировал запросы от обратного Nginx прокси на `192.168.5.128` (`client_ip=192.168.5.128`), так как IP отсутствовал в `TRUSTED_PROXIES` в `.env`.
  * **Решение**: В [`.env`](file:///d:/Projects/active/antigravity_bot/.env) добавлен параметр `TRUSTED_PROXIES=127.0.0.1,::1,192.168.5.128,192.168.5.107`.
  * **Стабилизация `run.py`**: В [`run.py`](file:///d:/Projects/active/antigravity_bot/run.py) функция `start_bot` обёрнута в цикл переподключения с перехватом сетевых ошибок `api.telegram.org` (WinError 121 / RST), чтобы сбои поллинга Telegram не роняли FastAPI веб-сервер.
  * **Верификация**: Проверены через Shellit MCP прямые вызовы к Nginx на `192.168.5.128`:
    * `GET /api/projects` -> HTTP 200 OK (список проектов возвращается).
    * `GET /api/projects/1/files` -> HTTP 200 OK (структура файлов и папок возвращается).
    * `GET /api/task_runs` -> HTTP 200 OK (история запусков заданий возвращается).

* **Деплой обновлённого Flutter Mini App 2.0 на сервер `192.168.5.128` (через MCP Shellit)**:
  * Подключились к серверу `192.168.5.128` (LXC-контейнер `AGY-Miniapp`, ID: `host-1791357556945`) через MCP-сервер `shellit`.
  * Создана резервная копия существующей рабочей папки `/var/www/html` в `/var/www/html_backup_*`.
  * Загружен и распакован свежий релизный бандл Flutter Mini App 2.0 (содержащий Chat History Viewer, File Explorer и Task Runs History).
  * Настроены права доступа `www-data:www-data`, перезагружен Nginx (`systemctl reload nginx`).
  * Проверена отдача статических файлов по HTTP (HTTP 200 OK) и проксирование запросов к бэкенду на `192.168.5.107:8000` (HTTP 200 OK).

* **Реализация Спринта 3: Flutter Mini App 2.0 (Chat Viewer, File Explorer, Task Runs)**:
  * **Просмотр истории диалога (Chat History Viewer)**:
    * В бэкенд FastAPI ([`src/server/app.py`](file:///d:/Projects/active/antigravity_bot/src/server/app.py)) добавлен эндпоинт `GET /api/sessions/{session_id}/messages`.
    * В экране бесед Mini App ([`SessionsScreen`](file:///d:/Projects/active/antigravity_bot/frontend_flutter/lib/screens/sessions_screen.dart)) внедрено модальное окно просмотра переписки: отображение сообщений пользователя и ответов агента, временных меток и форматирования.
  * **Встроенный проводник файлов и просмотрщик кода (Project File Explorer & Code Viewer)**:
    * В FastAPI добавлены защищённые эндпоинты `GET /api/projects/{project_id}/files?subdir=...` с проверкой на Path Traversal и `GET /api/projects/{project_id}/file_content?file_path=...` (с лимитом до 1 МБ).
    * В экране проектов ([`ProjectsScreen`](file:///d:/Projects/active/antigravity_bot/frontend_flutter/lib/screens/projects_screen.dart)) реализован компонент `_FileExplorerSheet`: навигация по подпапкам, переход на уровень выше (`..`), отображение размера файлов и модальный просмотр исходного кода в моноширинном шрифте.
  * **Журнал истории выполнения заданий (Task Runs History)**:
    * В экране планировщика ([`TasksScreen`](file:///d:/Projects/active/antigravity_bot/frontend_flutter/lib/screens/tasks_screen.dart)) добавлена кнопка и модальное окно просмотра истории запусков выбранной задачи: статусы (✅ Успешно, ❌ Ошибка), длительность в секундах, дата запуска и просмотр полного отчёта/ошибки.
  * **Сборка релизного бандла**:
    * Проведена компиляция `flutter build web --release` без ошибок.
    * Релизный бандл заново упакован в `miniapp_web.tar.gz` (14.2 МБ) для автономных установок и Docker-образов.

* **Автоматизация Публичного HTTPS (Nginx + Certbot Let's Encrypt) & Fix BUG-025**:
  * **Автоматизация SSL**: В мастер установки [`setup.py`](file:///d:/Projects/active/antigravity_bot/setup.py) внедрены функции `run_nginx_certbot_setup` и `configure_ssl_and_domain`. На серверах Linux мастер по введённому домену проверяет DNS (`socket.gethostbyname`), сам устанавливает `nginx`, `certbot`, `python3-certbot-nginx`, создаёт конфиг обратного прокси на `127.0.0.1:PORT`, открывает порты в UFW/firewalld, выпускает официальный сертификат Let's Encrypt и прописывает `WEBAPP_URL=https://<домен>`.
  * **Поддержка локального режима**: Для локальных ПК без домена предусмотрен явный пропуск настройки Mini App (кнопка в боте скрывается, бот работает на 100% через чат без ошибок безопасности Telegram).
  * **Исправление BUG-025**: В [`install.sh`](file:///d:/Projects/active/antigravity_bot/install.sh) восстановлен пропущенный закрывающий `fi` после блока распаковки веб-бандла.

* **Реализация Спринта 2: Упаковка, Документы, Артефакты, История Задач & Quick Actions**:
  * **Автономная установка `agy`**: В [`install.sh`](file:///d:/Projects/active/antigravity_bot/install.sh), [`install.ps1`](file:///d:/Projects/active/antigravity_bot/install.ps1) и интерактивный мастер [`setup.py`](file:///d:/Projects/active/antigravity_bot/setup.py) внедрена автоматическая загрузка и установка официального CLI Google Antigravity (`https://antigravity.google/cli/install.*`), если бинарник отсутствует в системе.
  * **Контейнеризация и службы**:
    * Создан легковесный [`Dockerfile`](file:///d:/Projects/active/antigravity_bot/Dockerfile) (Python 3.11-slim, ffmpeg, agy CLI, requirements, распаковка Flutter Web).
    * Создан [`docker-compose.yml`](file:///d:/Projects/active/antigravity_bot/docker-compose.yml) с сохранением томов данных (`data/`, `projects/`).
    * Создан production-ready шаблон службы [`deploy/antigravity-bot.service`](file:///d:/Projects/active/antigravity_bot/deploy/antigravity-bot.service) для Linux systemd.
  * **Мультимодальный приём документов**:
    * В Telegram-боте ([`src/bot/handlers/chat.py`](file:///d:/Projects/active/antigravity_bot/src/bot/handlers/chat.py)) реализован приём входящих файлов (`.log`, `.py`, `.txt`, `.json`, `.csv`, `.pdf` и др.) с сохранением и передачей агенту для моментального анализа.
  * **Автодоставка созданных артефактов**:
    * В [`src/agent/executor.py`](file:///d:/Projects/active/antigravity_bot/src/agent/executor.py) и [`src/agent/manager.py`](file:///d:/Projects/active/antigravity_bot/src/agent/manager.py) добавлен трекинг файлов, сгенерированных агентом инструментами (`write_to_file`, `create_file`, `generate_image`).
    * Все созданные артефакты автоматически отправляются пользователю в Telegram как файлы (`send_document`) как в интерактивном диалоге, так и при выполнении фоновых плановых заданий.
  * **История запусков заданий (`task_runs`)**:
    * В SQLite БД ([`src/database.py`](file:///d:/Projects/active/antigravity_bot/src/database.py)) создана таблица `task_runs` со связями Foreign Key, статусом, длительностью выполнения и preview вывода.
    * Планировщик ([`src/agent/scheduler.py`](file:///d:/Projects/active/antigravity_bot/src/agent/scheduler.py)) фиксирует запуск каждого задания, время выполнения и результат.
    * В FastAPI ([`src/server/app.py`](file:///d:/Projects/active/antigravity_bot/src/server/app.py)) добавлены защищённые эндпоинты `GET /api/task_runs` и `GET /api/tasks/{task_id}/runs`.
  * **Быстрые действия (Quick Actions)**:
    * В клавиатуру ([`src/bot/keyboards.py`](file:///d:/Projects/active/antigravity_bot/src/bot/keyboards.py)) и команды ([`src/bot/commands.py`](file:///d:/Projects/active/antigravity_bot/src/bot/commands.py)) добавлена кнопка «⚡ Действия» и команда `/quick` для быстрой диагностики: статус ОС/RAM/Диска, git статус, список файлов, запуск тестов.

* **Реализация Спринта 1: База Платформонезависимости & All-in-One**:
  * Полностью удалён хардкод Proxmox (`root@192.168.1.101`) из [`src/agent/manager.py`](file:///d:/Projects/active/antigravity_bot/src/agent/manager.py); внедрено динамическое автоопределение хоста и ОС (`platform.node()`, `platform.system()`, `platform.machine()`).
  * Реализован многоуровневый кроссплатформенный поиск `agy` (пользовательский путь из `.env`, системный PATH, стандартные директории Linux/macOS и Windows).
  * Параметры `agy_bin_path`, `system_context_hint` и `trusted_proxies` вынесены в конфигурацию [`src/config.py`](file:///d:/Projects/active/antigravity_bot/src/config.py) и [`.env.example`](file:///d:/Projects/active/antigravity_bot/.env.example).
  * Устранён хардкод IP-адресов в [`src/server/auth.py`](file:///d:/Projects/active/antigravity_bot/src/server/auth.py).
  * В [`src/server/app.py`](file:///d:/Projects/active/antigravity_bot/src/server/app.py) внедрён класс `SPAStaticFiles` с автоматическим fallback на `index.html` для полноценного хостинга Flutter Web без сторонних веб-серверов.
  * Созданы скрипты сборки веба: [`scripts/build_web.sh`](file:///d:/Projects/active/antigravity_bot/scripts/build_web.sh) и [`scripts/build_web.ps1`](file:///d:/Projects/active/antigravity_bot/scripts/build_web.ps1).
  * Создан интерактивный CLI-мастер установки [`setup.py`](file:///d:/Projects/active/antigravity_bot/setup.py) и полные автономные скрипты «Zero-to-Hero» установки в 1 команду:
    * [`install.sh`](file:///d:/Projects/active/antigravity_bot/install.sh) (Linux/macOS): сам определяет пакетный менеджер (`apt`, `dnf`, `pacman`), ставит Python 3.10+, pip, venv, curl, git, tar, распаковывает веб-бандл и регистрирует службу systemd.
    * [`install.ps1`](file:///d:/Projects/active/antigravity_bot/install.ps1) (Windows): сам ставит Python 3.11 через `winget` или официальный инсталлятор, настраивает окружение и базу данных.
  * Обновлена документация [`README.md`](file:///d:/Projects/active/antigravity_bot/README.md) с новыми инструкциями быстрой установки.

* **Утверждение Генерального Плана Развития (All-in-One Universal Hub)**:
  * По результатам обсуждения с пользователем скорректирован вектор развития: отказ от привязки к Proxmox в пользу 100% универсальности и переносимости платформы.
  * Сформулирован принцип «All-in-One»: Telegram-бот, FastAPI сервер, Flutter Mini App SPA, база данных SQLite и планировщик запускаются вместе на одной машине (локальный ПК, VPS или Docker).
  * В план включён интерактивный мастер установки в одну команду (`setup.py` / `install.sh`) с пошаговым CLI-диалогом для ввода токенов, админ ID, портов и режимов.
  * Генеральный документ плана полностью переписан и дополнен: [`wiki/development_proposals.md`](file:///d:/Projects/active/antigravity_bot/wiki/development_proposals.md).
  * Дорожная карта [`wiki/roadmap.md`](file:///d:/Projects/active/antigravity_bot/wiki/roadmap.md) и чеклист [`wiki/checklist.md`](file:///d:/Projects/active/antigravity_bot/wiki/checklist.md) разбиты на Спринты 1, 2 и 3.

### 2026-08-30
* **Инициализация проекта и архитектурное интервью (`/grill-me`)**:
  * Проведено детальное согласование требований (гибридный чат + Flutter TMA, SQLite, Antigravity).
  * Создан первичный документ архитектурного плана: [`wiki/implementation_plan.md`](file:///d:/Projects/active/antigravity_bot/wiki/implementation_plan.md).

* **Создание инфраструктуры документации (`wiki/`)**:
  * Создан каталог [`wiki/`](file:///d:/Projects/active/antigravity_bot/wiki/).
  * Разработана подробная дорожная карта: [`wiki/roadmap.md`](file:///d:/Projects/active/antigravity_bot/wiki/roadmap.md).
  * Инициализированы журнал активности, баг-трекер и чеклист.
  * Настроен агент-смотритель wiki (`.agents/skills/wiki-maintainer/` и правила `.agents/rules/`).

* **Реализация программной кодовой базы**:
  * Создано виртуальное окружение Python 3.11 (`venv/`) и установлены зависимости.
  * Реализован модуль базы данных SQLite [`src/database.py`](file:///d:/Projects/active/antigravity_bot/src/database.py).
  * Реализован движок агента [`src/agent/executor.py`](file:///d:/Projects/active/antigravity_bot/src/agent/executor.py) и [`src/agent/manager.py`](file:///d:/Projects/active/antigravity_bot/src/agent/manager.py).
  * Реализован Telegram-бот на `aiogram 3` (`src/bot/`).
  * Реализован FastAPI REST сервер (`src/server/`).
  * Реализован и скомпилирован Telegram Mini App на **Flutter Web** (`frontend_flutter/build/web/`).
  * Реализована единая точка запуска [`run.py`](file:///d:/Projects/active/antigravity_bot/run.py).

* **Развертывание LXC Контейнера 107 на Proxmox VE**:
  * Создан новый LXC-контейнер **CT 107 (`agy-miniapp`)** на хосте Proxmox VE (`pve-hp`).
  * Контейнеру выделен IP: `192.168.5.128`.
  * Внутри контейнера установлен и настроен веб-сервер `nginx` с поддержкой SPA-роутинга Flutter Web, сжатием gzip и кэшированием статических ресурсов.
  * Загружен и развернут релизный бандл Mini App в `/var/www/html`.

* **Интеграция Reverse Proxy и API-моста с локальным ПК**:
  * Настроен Nginx на CT 107: маршрут `/api/` проксируется на FastAPI бэкенд локального ПК (`http://192.168.5.107:8000`).
  * В Nginx Proxy Manager настроен защищенный хост `https://agy.bargcraft.top` с сертификатом Let's Encrypt.
  * Проверена работа API по HTTPS (`https://agy.bargcraft.top/api/status` возвращает `HTTP 200 OK`).
  * В [`.env`](file:///d:/Projects/active/antigravity_bot/.env) установлен `WEBAPP_URL=https://agy.bargcraft.top`.

* **Криптографическая защита Telegram WebApp Auth (TMA) & Доверенная сеть HomeLab**:
  * В [`src/server/auth.py`](file:///d:/Projects/active/antigravity_bot/src/server/auth.py) настроена гибридная многоуровневая авторизация:
    1. Автоматическое доверие локальной подсети HomeLab (`192.168.5.0/24`, `192.168.1.0/24`, `127.0.0.1`), откуда проксирует CT 107 (`192.168.5.128`).
    2. Полная проверка HMAC-SHA256 подписи Telegram при обращении из публичного интернета.
    3. Жесткая блокировка (`403 Forbidden`) для всех посторонних пользователей.

* **Встроенный фоновый планировщик автозаданий агента (`AgentScheduler`)**:
  * Добавлена таблица `scheduled_tasks` в SQLite БД.
  * Реализован модуль [`src/agent/scheduler.py`](file:///d:/Projects/active/antigravity_bot/src/agent/scheduler.py) с поддержкой времени `HH:MM` и `cron`.
  * Добавлен экран задач в Mini App (`TasksScreen`) и команды `/tasks`, `/add_task`.

* **Локальное распознавание речи (STT Whisper)**:
  * Входящие голосовые сообщения транскрибируются локально через нейросеть **`faster-whisper`** ([`src/agent/transcriber.py`](file:///d:/Projects/active/antigravity_bot/src/agent/transcriber.py)).

* **Преобразование Markdown в Telegram HTML & Исправление блоков кода**:
  * Реализован модуль [`src/bot/formatter.py`](file:///d:/Projects/active/antigravity_bot/src/bot/formatter.py) для надежного рендеринга форматирования, списков и блоков кода.

* **Оптимизация графа знаний Graphify (`.graphifyignore`)**:
  * Создан [`.graphifyignore`](file:///d:/Projects/active/antigravity_bot/.graphifyignore) для исключения тяжёлых скомпилированных веб-бандлов Flutter и WASM.
  * Объём анализируемого корпуса снижен с 323 265 до 19 893 слов, число узлов уменьшено с 7 131 до 427.
  * Файл [`graphify-out/graph.html`](file:///d:/Projects/active/antigravity_bot/graphify-out/graph.html) теперь открывается легко и плавно без нагрузки на систему.

* **Комплексный аудит и харденинг безопасности**:
  * **BUG-018 (Critical):** Устранена уязвимость обхода авторизации через spoofing IP-заголовков `X-Forwarded-For`. Заголовки больше не читаются; доверие только socket-level `request.client.host` для конкретных IP reverse proxy.
  * **BUG-019 (High):** Переведено на fail-closed: при `admin_id <= 0` доступ блокируется для всех (HTTP 503 / отказ в чате).
  * **BUG-020 (High):** Реализован полный цикл `confirm_mode`: метод `resolve_confirmation`, `_handle_permission_request` с `asyncio.Future`, `stdin=PIPE` для agy, перехват `ask_permission` tool events, клавиатура подтверждения, таймаут 120с.
  * **BUG-021 (Medium):** Добавлена проверка `is_task_running` в `handle_photo_message`.
  * Изображения из Telegram копируются в `workspace/.agy_uploads/` и добавляются через `--add-dir`.
  * Исправлено невалидное сочетание CORS `allow_origins=["*"]` + `allow_credentials=True`.
  * Bearer-токен проверяется через `hmac.compare_digest` только с `bot_token` (убран публичный `admin_id`).
  * Добавлена проверка свежести `auth_date` в `initData` (anti-replay, лимит 24ч).
  * **Устранение ложных предупреждений квоты:** Предупреждения `res.get("error")` теперь пишутся в лог и не добавляются в текст ответа, если модель успешно сгенерировала ответ.
  * **Защита от дедлока в scheduler и двойного подтверждения:** В `_handle_permission_request` при отсутствии коллбэка в `process.stdin` пишется явный отказ `b"n\n"`. Запрос подтверждения ограничен фазой `state == "ACTIVE"`.

* **Внедрение Скользящей Памяти Диалога (Sliding Window Memory)**:
  * Полностью устранён флаг `--conversation`, отправлявший в `agy` сотни килобайт сырого технического трейса инструментов (~450 000 токенов).
  * Реализована таблица `session_messages` в SQLite, хранящая чистую историю общения (запросы и ответы).
  * Перед каждым запросом динамически собирается компактный контекст из последних сообщений (~1 500 токенов).
  * Исправлена инициализация `conv_id` в `execute_turn`.
  * Интегрирована интеллектуальная политика безопасности для `confirm_mode`: информационные команды (диск, логи, статус) выполняются мгновенно, а любые деструктивные действия требуют явного согласования в чате.
* **Управление и удаление бесед (Session Deletion)**:
  * В меню бесед Telegram-бота (`/sessions`) рядом с каждой беседой добавлена кнопка «🗑» для быстрого удаления.
  * Реализован обработчик `cb_delete_session` с каскадным удалением сообщений и автоматическим назначением следующей активной сессии.
  * В интерфейс Flutter Mini App (`SessionsScreen`) добавлена кнопка удаления с диалоговым окном подтверждения.
  * Собран релизный бандл WebApp и успешно задеплоен на Nginx в контейнер Proxmox CT 107 (`https://agy.bargcraft.top`).

