# Legacy inventory and migration map (cleanup этап 2.1–2.3)

Документ фиксирует инвентаризацию production-кода вне `app/`, целевые пути и
фактический прогресс модульного переноса без `big bang`.

## 2.1 Инвентаризация кода вне `app/`

| Source | Status | Owner | Target date | Notes |
|---|---|---|---|---|
| `questionsapp/routes.py` | Delete (после полной декомиссии Flask entrypoint) | backend | 2026-04-30 | Оставлен как legacy-совместимость на период cutover. |
| `questionsapp/services/questions/*` | **Migrate (wave-1 completed)** | backend | 2026-04-13 | Перенесено в `app/services/legacy/questions/*`, старые файлы — import shims. |
| `questionsapp/services/roles/getrole.py` | **Migrate (wave-1 completed)** | backend | 2026-04-13 | Перенесено в `app/services/legacy/roles/getrole.py`, старый файл — shim. |
| `questionsapp/services/{attachments,appconfig,auxillary,questionslist,roles,stats,user,status}/*` | Migrate (planned) | backend | 2026-05-15 | Дальнейший перенос по доменам без изменения API-контрактов. |
| `supp_db/*` | Keep as infra (temporary) | backend + dba | 2026-05-01 | Вынести SQL-код в `app/repositories/` по приоритету сценариев. |
| `database.py` | Migrate | backend | 2026-05-01 | Переместить в `app/db/` после консолидации session lifecycle. |
| `config.py` (root) | Delete (после единого config source) | backend | 2026-05-01 | Дубликат runtime-конфигурации, целевой источник `app/core/config.py`. |
| `celery_worker.py` | Migrate | backend | 2026-05-10 | Перенос в `app/workers/` на этапе 4.1. |
| `tasks/*` | Migrate | backend | 2026-05-10 | Перенос в `app/workers/tasks/*` с доменной декомпозицией. |

## 2.2 Целевая структура и mapping legacy → app

| Legacy path | Target path in `app/` | Rationale |
|---|---|---|
| `questionsapp/services/questions/*` | `app/services/legacy/questions/*` | Изоляция legacy-домена под `app/` без переписывания бизнес-логики. |
| `questionsapp/services/roles/getrole.py` | `app/services/legacy/roles/getrole.py` | Общий helper, используемый question-domain сценариями. |
| `questionsapp/services/questionslist/*` | `app/services/legacy/questionslist/*` → далее `app/services/questions/*` | Поэтапный перенос read-side API list/filters. |
| `questionsapp/services/attachments/*` | `app/services/legacy/attachments/*` → далее `app/services/attachments/*` | Сначала перенос 1-в-1, затем декомпозиция на repository/gateway. |
| `questionsapp/services/appconfig/*` | `app/services/legacy/appconfig/*` → `app/core/config_runtime.py` | Убираем доступ к runtime-конфигу из endpoint-слоя. |
| `questionsapp/services/auxillary/*` | `app/integrations/*` и `app/core/*` | Telegram/SQL utility функции будут оформлены как gateways. |
| `questionsapp/services/stats/*` | `app/services/legacy/stats/*` → `app/services/stats/*` | Статистика переносится доменно, без смешивания с HTTP-слоем. |
| `supp_db/*` | `app/repositories/supp_db/*` | SQL и доступ к данным должны жить в repository-слое. |
| `database.py` | `app/db/{engine.py,session.py}` | Единый жизненный цикл DB в FastAPI DI. |
| `celery_worker.py`, `tasks/*` | `app/workers/*` | Унифицированный worker bootstrap и доменные jobs. |

## 2.3 Модульный перенос (wave-1)

### Выполнено
1. Перенесен домен `questions` из `questionsapp/services/questions/*` в
   `app/services/legacy/questions/*`.
2. Перенесен helper `roles/getrole.py` в `app/services/legacy/roles/getrole.py`.
3. Обновлены импорты в FastAPI bridge и связанных legacy-модулях на новый namespace `app.services.legacy.*`.
4. Для Flask-legacy entrypoint оставлены совместимые shim-файлы в `questionsapp/services/*`,
   которые только реэкспортируют реализацию из `app/`.

### Definition of Done for wave-1
- В проекте одна активная реализация question-domain логики — в `app/services/legacy/questions/*`.
- Legacy namespace используется только как временный слой совместимости импорта.
- API-контракт не изменен, так как бизнес-логика и response envelopes не переписывались.
