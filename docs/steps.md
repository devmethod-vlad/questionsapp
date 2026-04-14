1) Подготовка и инвентаризация (эпики/тикеты)
1.1 Снять “слепок” текущего Flask API
Список всех endpoint’ов: method, path, query/body/path params, headers.

Форматы успешных и ошибочных ответов (включая коды, тексты ошибок, nullable-поля, порядок ключей если критично).

Особые кейсы: кастомные сериализации дат, Decimal, enum, пустые тела и т.п.

Авторизация/аутентификация и middleware-поведение.

1.2 Зафиксировать non-functional baseline
Метрики latency/error rate.

Логи/трейсы (если есть) для сравнения после миграции.

2) Создание каркаса FastAPI (без бизнес-изменений)
2.1 Новый app skeleton
app/main.py (инициализация FastAPI)

app/api/v1/... (роутеры)

app/core/config.py (настройки)

app/schemas/... (Pydantic-модели)

app/services/... (бизнес-логика)

app/repositories/... (доступ к данным)

2.2 Настройка инфраструктуры
Uvicorn/Gunicorn ASGI запуск.

Централизованный handling ошибок.

CORS, middleware, request-id, health-check endpoint.

Логирование в едином формате.

2.3 Совместимые HTTP-ответы
Ввести общий слой response builders, чтобы сохранить старые форматы.

Явно реализовать старые error envelopes (если во Flask были нестандартные).

3) Pydantic-валидация без ломки контрактов
3.1 Request-схемы
Для каждого endpoint создать входную модель.

Настроить alias/field name mapping, если у старого API нестандартные имена.

Разрешить “лишние” поля (extra) там, где старый API их терпел (на старте).

3.2 Response-схемы
Описать модели ответа, но отдавать точно тот же JSON.

Если раньше были “гибкие” поля — использовать union/optional/кастомные сериализаторы.

3.3 Совместимость ошибок валидации
По умолчанию FastAPI даёт 422 со своей структурой.

Если у вас раньше другое тело/код ошибки — перехватить RequestValidationError и вернуть legacy-формат.

4) Перенос endpoint’ов (итерационно)
4.1 Стратегия миграции
По доменам: users/orders/... или по критичности.

На каждый endpoint:

перенос route,

подключение схем,

адаптер к старой бизнес-логике,

прогон контрактных тестов.

4.2 Минимизация риска
Бизнес-логику не переписывать сразу: вынести из Flask в сервисный слой и переиспользовать.

Временные адаптеры “Flask-style -> FastAPI-style”.

5) Доступ к данным и транзакции
Унифицировать session management (особенно если SQLAlchemy).

Явно определить lifecycle dependency (Depends) для DB session.

Проверить транзакционное поведение 1-в-1 (commit/rollback timing).

Проверить pooling/timeouts в ASGI-контексте.


6) Документация и эксплуатация
Актуальная OpenAPI-спека.

Migration checklist для каждого endpoint.

Changelog по совместимости (должен быть “no breaking changes”).

7) Финальный cutover
100% endpoint’ов в FastAPI.

Полное переключение.

Удаление Flask-слоя и временных адаптеров.


---

## Выполнено в текущей итерации (шаги 4.1, 4.2, 5)

### 4.1 Стратегия миграции (реализация)
- Роуты FastAPI разбиты по доменам (`meta`, `questions`) вместо одного большого файла endpoint'ов.
- Добавлены доменные адаптеры сервисного слоя (`LegacyQuestionHandlers`, `LegacyAdminHandlers`) для явной связки: `route -> schema -> adapter -> legacy service`.
- Каждый endpoint по-прежнему использует существующую бизнес-логику без изменения контракта входа/выхода.

### 4.2 Минимизация риска
- Бизнес-логика Flask не переписывалась: используется через bridge/adapters.
- Введён временный переходный слой (`app/services/legacy/*`), который изолирует FastAPI-роуты от низкоуровневой legacy-реализации.
- Сохранены legacy-форматы ошибок и успешных ответов на уровне response builders.

### 5 Доступ к данным и транзакции
- Добавлена явная FastAPI dependency для lifecycle управления legacy SQLAlchemy session:
  - rollback при необработанном исключении;
  - remove в `finally` для освобождения scoped session в ASGI-контексте.
- Dependency подключена к мигрированным endpoint'ам, что фиксирует единое поведение cleanup между запросами.

## Выполнено в текущей итерации (шаги 6, 7)

### 6 Документация и эксплуатация
- Сгенерирована и зафиксирована актуальная OpenAPI-спека: `docs/openapi.json`.
- Добавлен migration checklist по endpoint-совместимости: `docs/migration_checklist.md`.
- Добавлен compatibility changelog с фиксацией `no breaking changes`: `docs/compatibility_changelog.md`.

### 7 Финальный cutover
- Основной контейнерный HTTP runtime переключён на FastAPI ASGI (`uvicorn app.main:app`).
- Временные роутер-адаптеры удалены, вместо них используется стабильный сервисный слой:
  - `app/services/questions_service.py`
  - `app/services/admin_service.py`
- Legacy bridge path выведен из active runtime; FastAPI-инфраструктура не зависит от Flask runtime при импортах.


## Следующий этап
- Детальный план финальной очистки и декомиссии Flask: `docs/post_fastapi_cleanup_plan.md`.

## Выполнено в текущей итерации (post-cleanup шаги 3.1, 3.2, 3.3)

### 3.1 Единый DB lifecycle
- Введён единый request-scoped lifecycle dependency: `app/db/session.py`.
- Политика rollback/remove централизована в одном месте и используется FastAPI endpoint'ами.
- Совместимый shim `app/repositories/legacy_session.py` удалён после перевода активных импортов на `app/db/session.py`.

### 3.2 Репозитории вместо SQL в handlers
- Добавлен контракт репозитория `QuestionsReadRepository` и SQLAlchemy-реализация
  `SqlAlchemyQuestionsReadRepository` в `app/repositories/questions_repository.py`.
- SQL для `/questions_api/` вынесен из legacy handler в repository-слой.
- Сервисный слой теперь использует dependency-инъекцию (`app/services/dependencies.py`) и вызывает репозиторий по цепочке:
  `endpoint -> service -> repository`.

### 3.3 Асинхронность (отдельный трек)
- Подготовлен отдельный RFC/беклог на async data layer:
  `docs/async_data_layer_rfc.md`.
- Cleanup-итерация не смешивается с async-миграцией; текущий sync-контур стабилизирован.
