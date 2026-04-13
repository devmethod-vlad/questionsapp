# FastAPI migration architecture (Steps 2.1–2.3)

## Структура

- `app/main.py` — инициализация FastAPI приложения.
- `app/api/v1/` — versioned роутеры и endpoint handlers.
- `app/core/config.py` — настройки на `pydantic-settings`.
- `app/core/exceptions.py` — централизованная обработка ошибок.
- `app/core/middleware.py` — `request-id` и request logging middleware.
- `app/schemas/` — Pydantic-модели входных данных.
- `app/services/legacy_bridge.py` — bridge к текущим Flask services без изменения бизнес-логики.
- `app/responses/builders.py` — совместимые response builders (legacy envelopes).
- `app/repositories/` — место для будущего выноса data access слоя.

## Принципы совместимости

1. Сохранены исходные URL и payload форматы (`/eduportal/questions/...`).
2. Для action-based endpoint’ов сохранён envelope:
   - успех: `{"status":"ok"}` (или legacy payload)
   - ошибка: `{"status":"error","error_mess":"..."}`
3. Для `/questions_api/` сохранён отдельный формат пагинации.
4. Валидация Pydantic добавлена в permissive режиме (`extra="allow"`),
   чтобы не ломать существующих клиентов.

## Инфраструктура

- CORS включается централизованно.
- Добавлен healthcheck endpoint: `GET /health`.
- Включён `X-Request-ID` middleware.
- Логи запросов и приложения — в JSON-формате.
- Глобальные exception handlers маппят ошибки в legacy envelopes.

## Запуск (ASGI)

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

или через Gunicorn:

```bash
gunicorn -k uvicorn.workers.UvicornWorker app.main:app -b 0.0.0.0:8000
```
