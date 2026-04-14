# План финальной очистки проекта после миграции на FastAPI

> **Status (2026-04-14):** Historical planning document. Several bridge-related items are already completed in code; use it as archive/backlog context, not as current architecture source.


Цель: полностью убрать наследие Flask, собрать весь production-код в `app/`, и при этом **не менять внешние API-контракты** (URL, формат входов/выходов, коды ответов).

---

## Принципы выполнения

1. Сначала фиксируем контракт (snapshot), потом удаляем legacy.
2. Любое удаление делаем только после замены и проверки эквивалентности.
3. Фокус на «тонкий API-слой + сервисы + репозитории», без бизнес-логики в endpoint-файлах.
4. Каждый шаг оформляется как отдельная задача с измеримым DoD.

---

## Этап 0. Защитный периметр перед чисткой

### 0.1 Зафиксировать «что нельзя сломать»
- Использовать уже сохранённые артефакты (`docs/flask_api_snapshot.md`, `docs/openapi.json`, `docs/compatibility_changelog.md`).
- Добавить таблицу endpoint-совместимости: `method/path`, обязательные поля, коды ответов, envelope ошибок.

**DoD:** есть единый документ-источник правды по контрактам, на который ссылаются все последующие задачи.
---

## Этап 1. Удалить Flask из runtime

### 1.1 Убрать Flask как обязательную зависимость
- Пересобрать зависимости: удалить `Flask`, `Flask-Cors`, `Flask-Limiter`, `Flask-SQLAlchemy` из `pyproject.toml` после миграции к FastAPI-аналогам.
- Проверить, что импорты Flask больше не используются в коде runtime.

**DoD:** приложение запускается без Flask-пакетов.

### 1.2 Удалить Flask entrypoints
- Удалить/архивировать `wsgi.py` и любые команды запуска, ведущие в Flask app factory.
- Оставить единственный production entrypoint: `app.main:app`.

**DoD:** в проекте ровно один HTTP entrypoint (ASGI).

### 1.3 Вычистить Flask app-factory bridge
- Постепенно убрать зависимость `app/services/legacy_bridge.py` от Flask-контекста.
- Перевести оставшиеся вызовы на «чистые» сервисы/репозитории без `current_app`, `g`, flask session lifecycle.

**DoD:** `legacy_bridge` либо удалён, либо сведён к техническому адаптеру без Flask import'ов.

---

## Этап 2. Перенести production-код под `app/`

### 2.1 Инвентаризация кода вне `app/`
Папки/файлы-кандидаты на разбор:
- `questionsapp/`
- `supp_db/`
- `database.py`, `config.py`, `celery_worker.py`, `tasks/`

Для каждого элемента определить статус:
- **Migrate** (перенести в `app/`),
- **Keep as infra** (оставить в корне, если это инфраструктурный entrypoint),
- **Delete** (устарело).

**DoD:** есть таблица миграции файлов с владельцем и целевой датой.

### 2.2 Новая целевая структура (ориентир)
- `app/api/` — только роутинг/DTO/DI
- `app/services/` — бизнес-правила
- `app/repositories/` — доступ к данным
- `app/db/` — engine/session/models/migrations hooks
- `app/workers/` — celery tasks и jobs
- `app/core/` — config/logging/errors/security

**DoD:** для каждой legacy-папки определён точный target path в новой структуре.

### 2.3 Миграция модулями (без big bang)
- Переносить по доменам (например, `questions`, `roles`, `attachments`), а не по техническим слоям сразу.
- На каждый перенос:
  1) move/import rewrite,
  2) удаление старого дубля.

**DoD:** в репозитории не остаётся одновременно двух активных реализаций одного и того же доменного сценария.

---

## Этап 3. Привести data layer к FastAPI-паттерну

### 3.1 Единый DB lifecycle
- Убрать legacy-scoped session-поведение из старых модулей.
- Ввести единый dependency/provider для транзакций (request-scoped) и явный rollback policy.

**DoD:** все HTTP-сценарии используют один способ получения DB session.

### 3.2 Репозитории вместо SQL в endpoint/handlers
- Вынести SQL/ORM операции из legacy handlers в `app/repositories/*`.
- Сервисы работают через интерфейсы репозиториев.

**DoD:** endpoint -> service -> repository; прямой работы с БД в endpoint нет.

### 3.3 Асинхронность (опционально, после стабилизации)
- Не форсировать async миграцию сразу.
- Сначала стабилизировать sync-цепочку, затем отдельно оценить async SQLAlchemy/driver.

**DoD:** есть отдельный RFC/задача на async, не смешанная с cleanup-итерацией.

---

## Этап 4. Унифицировать фоновые задачи и интеграции

### 4.1 Перенести Celery-слой в `app/workers`
- Переместить `celery_worker.py` и `tasks/*` в модульную структуру доменных задач.
- Описать единый bootstrap worker-конфигурации.

**DoD:** worker стартует из нового пути, старые entrypoint-файлы удалены.

### 4.2 Явные контракты для внешних интеграций
- Telegram/Atlassian/прочие интеграции скрыть за gateway-классами (`app/integrations/*`).
- Добавить retry/timeout policy и наблюдаемость (логи, correlation id).

**DoD:** внешние вызовы не разбросаны по endpoint-обработчикам.

---

## Этап 5. Удаление мусора и консолидация конфигурации

### 5.1 Единый конфиг
- Свести runtime-настройки к `app/core/config.py`.
- Удалить дубли в корневых `config.py`/env-модулях после миграции.

**DoD:** все runtime настройки читаются из одного источника.

### 5.2 Очистка неиспользуемых файлов
- Удалить неиспользуемые legacy templates/static, если они больше не обслуживаются API.
- Проверить, что не осталось «мертвых» импортов и orphan-модулей.

**DoD:** `rg` по legacy-неймспейсам не находит runtime-использования.

---

## Этап 6. Codex-ready backlog (формат задач)

Ниже шаблон одной задачи, чтобы легко переносить в Codex:

### Task template
**Title:** `[Cleanup] <краткое действие>`

**Context:**
- Почему делаем (ссылка на этап/подэтап).
- Какие контракты нельзя менять.

**Scope:**
- Файлы/папки, которые можно менять.
- Что точно вне scope.

**Implementation steps:**
1. ...
2. ...
3. ...

**Definition of Done:**
- [ ] ...
- [ ] ...

**Checks:**
- `pytest <targeted tests>`
- `rg "<legacy import pattern>"`
- `uvicorn app.main:app --host 127.0.0.1 --port 8000` (smoke)

---
