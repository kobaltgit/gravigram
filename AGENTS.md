# Инструкции Проекта и Правила Агентов

## Обязательное ведение каталога `wiki/`
Вы работаете в проекте **Antigravity Telegram Bot & Flutter Mini App**.

Каждый раз, когда вы вносите изменения в проект, исправляете ошибки или планируете новые задачи, вы обязаны соблюдать правила из [`.agents/rules/wiki_rules.md`](file:///d:/Projects/active/antigravity_bot/.agents/rules/wiki_rules.md):

1. **`wiki/activity_log.md`**: Добавлять новую запись обо всех созданных или измененных компонентах.
2. **`wiki/checklist.md`**: Обновлять статус задач (`[x]`, `[/]`, `[ ]`).
3. **`wiki/bug_tracker.md`**: Регистрировать найденные баги и закрывать исправленные.
4. **`wiki/roadmap.md`**: Поддерживать соответствие дорожной карты текущему прогрессу.

## Стек Проекта
* Python 3.10+ (asynchronous: `asyncio`)
* `aiogram 3` (Telegram Bot Framework)
* `google-antigravity` SDK (Antigravity Agent Engine)
* `fastapi` + `uvicorn` (REST API & Mini App Hosting)
* `aiosqlite` (Async SQLite Database)
* **Flutter 3.44+ / Dart** (`frontend_flutter/` — Telegram Mini App SPA)

## Управление Планировщиком Задач (Scheduled Tasks)
Если пользователь просит запланировать, изменить или удалить задачу по расписанию (например, *"запланируй утренний аудит серверов в 09:00"*, *"каждый день в 10:00 запускай тесты"*, *"удали задачу #1"*):
* Выполните команду через инструмент `run_command`:
  * Создать: `python -m src.agent.schedule_cli add --time "09:00" --prompt "Промпт для агента" --title "Название задачи"`
  * Список: `python -m src.agent.schedule_cli list`
  * Удалить: `python -m src.agent.schedule_cli delete --id <id>`
  * Включить/Пауза: `python -m src.agent.schedule_cli toggle --id <id> --active true|false`
* Подтвердите пользователю успешное создание задания и время следующего выполнения.
