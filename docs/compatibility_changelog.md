# Compatibility changelog

## 2026-04-13 — Migration steps 6 and 7 completed

### No breaking changes

- URL префикс API сохранён (`/eduportal/questions`).
- Форматы входных данных и ответов сохранены для всех перенесённых API endpoint’ов.
- Legacy-формат ошибок сохранён для бизнес- и validation-ошибок.

### Internal changes (safe for clients)

- Введён стабильный service layer FastAPI (`QuestionsService`, `AdminService`) вместо временных роутер-адаптеров.
- Legacy Flask app инициализируется лениво только при фактическом обращении к legacy сервисам.
- Обновлён deployment cutover: основной HTTP-процесс запускается через FastAPI/ASGI.

### Operational artifacts

- Добавлен migration checklist для контроля совместимости.
- Добавлен и зафиксирован актуальный OpenAPI snapshot (`docs/openapi.json`).
