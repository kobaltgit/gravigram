---
name: wiki-maintainer
description: "Автоматическое управление, аудит и поддержание в актуальном состоянии всей проектной документации в каталоге wiki (activity_log, checklist, bug_tracker, roadmap). Активируйте этот навык после завершения задач или при обнаружении багов."
---

# Wiki Maintainer Skill

Данный навык предназначен для поддержания идеального порядка и актуальности каталога `wiki/` в проекте.

## Обязанности Навыка

При каждом цикле разработки или по запросу пользователя навык выполняет следующие шаги:

1. **Анализ активности (Activity Log Sync)**:
   * Проверяет недавние изменения в кодовой базе (`git status` или список затронутых файлов).
   * Добавляет запись в [`wiki/activity_log.md`](file:///d:/Projects/active/antigravity_bot/wiki/activity_log.md) в хронологическом порядке.

2. **Обновление Чеклиста (Checklist Sync)**:
   * Открывает [`wiki/checklist.md`](file:///d:/Projects/active/antigravity_bot/wiki/checklist.md).
   * Находит выполненные `TASK-XXX` и меняет их статус на `[x]`.
   * Если добавлены новые подзадачи, аккуратно интегрирует их в соответствующий раздел.

3. **Синхронизация Багов (Bug Tracker Sync)**:
   * Открывает [`wiki/bug_tracker.md`](file:///d:/Projects/active/antigravity_bot/wiki/bug_tracker.md).
   * Если найден баг — генерирует новый `BUG-XXX` с описанием и шагами воспроизведения.
   * Если баг устранен — переводит статус в `🟢 Resolved` / `⚪ Verified` и проставляет решение.

4. **Синхронизация Дорожной Карты (Roadmap Sync)**:
   * Открывает [`wiki/roadmap.md`](file:///d:/Projects/active/antigravity_bot/wiki/roadmap.md).
   * Сверяет прогресс по фазам и вехам, обновляет диаграмму Mermaid и чеклисты фаз.
