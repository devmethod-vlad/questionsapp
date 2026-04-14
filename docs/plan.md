### Task 1

> **Status (2026-04-14):** Historical planning document. Several bridge-related items are already completed in code; use it as archive/backlog context, not as current architecture source.


**Title:** `[Cleanup] Remove current_app-based config helpers from app runtime`

**Context:**
FastAPI routes are already native, but several helper modules still require Flask app context only to read config values. This blocks bridge removal and keeps Flask in the runtime path. External API contracts must remain unchanged.

**Scope:**

* `app/services/legacy/roles/getrole.py`
* `questionsapp/services/status/transformstatuslist.py`
* `app/services/legacy/questions/get_questions_api.py`
* `app/core/config.py`
* new helper modules under `app/core/` or `app/services/common/`

**Implementation steps:**

1. Introduce plain app-side config accessors/constants for role/status/null-space/url-prefix values.
2. Replace `current_app.config[...]` usage in the listed helpers with direct app-side config access.
3. Remove Flask imports from these helpers.
4. Keep all return formats and business behavior unchanged.

**Definition of Done:**

* [ ] Listed modules no longer import `flask` or `current_app`
* [ ] `/questions_api/` helper path works without Flask app context for config reads
* [ ] No external API contract changes

**Checks:**

* `rg "current_app|from flask" app/services/legacy/roles/getrole.py questionsapp/services/status/transformstatuslist.py app/services/legacy/questions/get_questions_api.py`
* `uvicorn app.main:app --host 127.0.0.1 --port 8000`

---

### Task 2

**Title:** `[Cleanup] Remove legacy bridge usage from questions_api endpoint`

**Context:**
`/questions_api/` already has a repository abstraction and is the easiest endpoint to make fully native. External response format must stay unchanged.

**Scope:**

* `app/api/v1/endpoints/questions.py`
* `app/services/questions_service.py`
* `app/services/dependencies.py`
* `app/repositories/questions_repository.py`
* `app/services/legacy/questions/get_questions_api.py`
* `app/services/legacy_bridge.py`

**Implementation steps:**

1. Make `QuestionsService.get_public_questions()` call the repository directly instead of `LegacyServiceAdapter.get_questions_api(...)`.
2. Move remaining pagination normalization and config access to native service/repository code.
3. Delete `LegacyServiceAdapter.get_questions_api(...)` usage.
4. Keep the JSON structure of `/questions_api/` unchanged.

**Definition of Done:**

* [ ] `/questions_api/` path no longer depends on `legacy_bridge.py`
* [ ] No Flask context is needed to serve `/questions_api/`
* [ ] Response payload structure stays byte-for-byte compatible at field level

**Checks:**

* `rg "get_questions_api\\(" app/services app/api`
* `rg "LegacyServiceAdapter.get_questions_api" app`
* `uvicorn app.main:app --host 127.0.0.1 --port 8000`

---

### Task 3

**Title:** `[Cleanup] Migrate spaceandroles and small admin actions to native app services`

**Context:**
Several small action-based flows still pass through the legacy bridge even though their logic is relatively compact. This is low-risk cleanup with high payoff for bridge reduction.

**Scope:**

* `app/services/admin_service.py`
* `app/services/legacy_bridge.py`
* `questionsapp/services/auxillary/getrolesbyspace.py`
* `questionsapp/services/roles/createnewadmin.py`
* `questionsapp/services/roles/changeadminpass.py`
* `questionsapp/services/roles/enteradmin.py`
* `questionsapp/services/roles/exitadmin.py`
* `questionsapp/services/appconfig/getappconfig.py`
* `questionsapp/services/appconfig/updateconfig.py`
* new native modules under `app/services/` and `app/repositories/`

**Implementation steps:**

1. Create native service modules for roles/admin/appconfig scenarios under `app/services/`.
2. Move ORM access into repository helpers where useful.
3. Replace `current_app` config reads with app-side config provider usage.
4. Update `AdminService` to call native modules directly.
5. Remove corresponding branches from `LegacyServiceAdapter.service_action(...)` and `get_roles(...)` as they become unused.

**Definition of Done:**

* [ ] `spaceandroles` no longer goes through `legacy_bridge.py`
* [ ] Admin/appconfig actions no longer require Flask app context
* [ ] JSON success/error envelopes remain unchanged

**Checks:**

* `rg "LegacyServiceAdapter.get_roles|LegacyServiceAdapter.service_action" app`
* `rg "from flask|current_app" app/services questionsapp/services/roles questionsapp/services/auxillary/getrolesbyspace.py`
* `uvicorn app.main:app --host 127.0.0.1 --port 8000`

---

### Task 4

**Title:** `[Cleanup] Extract questionslist into native service and repository layer`

**Context:**
`questionslist` still lives in a large legacy module with raw SQL orchestration, direct engine creation, Flask config access, and response shaping mixed together. This keeps bridge and Flask context alive.

**Scope:**

* `questionsapp/services/questionslist/formquestionslist.py`
* `supp_db/queries/questions.py`
* `app/services/questions_service.py`
* `app/services/legacy_bridge.py`
* new modules under `app/services/` and `app/repositories/`

**Implementation steps:**

1. Split `formquestionslist` into:

   * native service for request orchestration and response shaping,
   * repository for SQL execution,
   * pure helper functions for filters and transformations.
2. Replace `create_engine(app.config['SQLALCHEMY_DATABASE_URI'])` with app-side engine/session access.
3. Remove `current_app` usage by routing all config access through app-side config helpers.
4. Update `QuestionsService.get_questions_list(...)` to call the native service directly.
5. Remove the corresponding `LegacyServiceAdapter.form_questions_list(...)` dependency.

**Definition of Done:**

* [ ] `/questionslist/` no longer requires Flask app context
* [ ] No direct `create_engine(...)` call remains in the endpoint domain logic
* [ ] Legacy response structure remains unchanged

**Checks:**

* `rg "create_engine\\(" questionsapp/services/questionslist app/services app/repositories`
* `rg "LegacyServiceAdapter.form_questions_list" app`
* `uvicorn app.main:app --host 127.0.0.1 --port 8000`

---

### Task 5

**Title:** `[Cleanup] Introduce native file upload abstraction and remove FileCompat dependence`

**Context:**
`legacy_bridge.FileCompat` is a fragile compatibility shim for FastAPI uploads. Legacy save handlers expect Flask-style file objects and also read attributes like `content_length`, which makes the current bridge brittle.

**Scope:**

* `app/services/legacy_bridge.py`
* `app/services/questions_service.py`
* `app/services/legacy/questions/savequestion.py`
* `app/services/legacy/questions/saveanswer.py`
* new modules under `app/services/files/` or similar

**Implementation steps:**

1. Introduce an application-level upload abstraction with explicit fields/methods needed by business logic:

   * filename
   * size_bytes
   * save_to(path)
2. Update save-question/save-answer flows to consume this abstraction instead of Flask/Werkzeug-style objects.
3. Remove reliance on `.content_length` from legacy-compatible code paths.
4. Keep external multipart field names and API response payloads unchanged.

**Definition of Done:**

* [ ] File save flows no longer depend on Flask/Werkzeug upload semantics
* [ ] `FileCompat` is either deleted or no longer used by active code
* [ ] Multipart API contract stays unchanged

**Checks:**

* `rg "FileCompat|content_length|save\\(" app/services`
* `uvicorn app.main:app --host 127.0.0.1 --port 8000`

---

### Task 6

**Title:** `[Cleanup] Migrate question write flows out of legacy bridge`

**Context:**
The main write scenarios (`save_question`, `save_answer`, `save_combine`, `save_anonym_question`, `exec_action`) still contain mixed business rules, DB writes, file operations, notifications, and task dispatch. This is the largest remaining Flask-bound domain.

**Scope:**

* `app/services/legacy/questions/savequestion.py`
* `app/services/legacy/questions/saveanswer.py`
* `app/services/legacy/questions/savecombine.py`
* `app/services/legacy/questions/saveanonymquestion.py`
* `app/services/legacy/questions/execaction.py`
* `app/services/questions_service.py`
* `app/services/admin_service.py`
* `app/services/legacy_bridge.py`
* new modules under `app/services/`, `app/repositories/`, `app/integrations/`, `app/files/`

**Implementation steps:**

1. Split write flows into native command services:

   * save question
   * save answer
   * save combined question+answer
   * save anonymous question
   * execute service actions on questions
2. Move DB access patterns into repositories.
3. Move Telegram sending behind an integration gateway.
4. Move file-system writes behind file storage helpers.
5. Keep all API envelopes, action names, and field names unchanged.
6. Remove corresponding branches from `LegacyServiceAdapter.save_or_update(...)` and `service_action(...)`.

**Definition of Done:**

* [ ] `/saveorupdate/` no longer requires Flask app context
* [ ] `execaction` flow no longer requires Flask app context
* [ ] Active write flows do not import `current_app` or `database.db`

**Checks:**

* `rg "LegacyServiceAdapter.save_or_update|LegacyServiceAdapter.service_action" app`
* `rg "from flask|current_app|from database import db" app/services/legacy/questions app/services`
* `uvicorn app.main:app --host 127.0.0.1 --port 8000`

---

### Task 7

**Title:** `[Cleanup] Remove Flask dependencies from worker tasks and integrations`

**Context:**
Even after HTTP flows are migrated, Flask remains a runtime dependency because Celery tasks and support DB helpers still use `current_app`, `database.db`, and legacy namespaces.

**Scope:**

* `app/workers/tasks/publicorder.py`
* `app/workers/tasks/updatespaceinfo.py`
* `app/workers/tasks/updatespaceinfo_new.py`
* `supp_db/supp_connection.py`
* related integration/bootstrap modules
* new modules under `app/integrations/`, `app/workers/`, `app/db/`

**Implementation steps:**

1. Replace `current_app` config reads in tasks with app-side config providers.
2. Replace `database.db` usage with native session providers.
3. Move Oracle DSN creation out of Flask-bound helper code.
4. Keep Celery task names and side effects unchanged.
5. Ensure worker bootstrap does not require Flask app factory.

**Definition of Done:**

* [ ] Worker tasks no longer import `flask` or `current_app`
* [ ] Support DB connection code no longer depends on Flask config
* [ ] Worker runtime can start without Flask app factory

**Checks:**

* `rg "from flask|current_app" app/workers supp_db`
* `rg "from database import db" app/workers supp_db`
* worker smoke startup command from project docs or compose config

---

### Task 8

**Title:** `[Cleanup] Replace Flask-SQLAlchemy with native SQLAlchemy session management`

**Context:**
The current FastAPI request session layer still wraps `db.session` from `flask_sqlalchemy`, so Flask remains embedded in the data layer.

**Scope:**

* `database.py`
* `app/db/session.py`
* repository/session providers under `app/`
* worker session providers
* legacy modules still importing `database.db`

**Implementation steps:**

1. Introduce native SQLAlchemy engine and sessionmaker under `app/db/`.
2. Update `RequestSessionContext` to use native SQLAlchemy sessions instead of `db.session`.
3. Migrate repositories and active services to the new session provider.
4. Remove Flask-SQLAlchemy dependency from active runtime paths.
5. Keep transactional behavior equivalent for current sync flows.

**Definition of Done:**

* [ ] `app/db/session.py` no longer depends on `database.db`
* [ ] Active runtime path no longer depends on Flask-SQLAlchemy
* [ ] Request lifecycle uses native SQLAlchemy session management

**Checks:**

* `rg "from database import db" app`
* `rg "flask_sqlalchemy|SQLAlchemy\\(" .`
* `uvicorn app.main:app --host 127.0.0.1 --port 8000`

---

### Task 9

**Title:** `[Cleanup] Delete legacy bridge and Flask runtime path`

**Context:**
After all active flows are migrated, the bridge and Flask app factory should be removed to complete the cleanup.

**Scope:**

* `app/services/legacy_bridge.py`
* `questionsapp/__init__.py`
* `questionsapp/routes.py`
* remaining unused legacy modules
* startup/bootstrap references

**Implementation steps:**

1. Remove all remaining imports/usages of `LegacyServiceAdapter` and `FileCompat`.
2. Delete bridge code, Flask app factory bootstrap, and legacy route module from active runtime path.
3. Remove dead imports and stale compatibility shims.
4. Keep only `app.main:app` as the HTTP runtime entrypoint.

**Definition of Done:**

* [ ] `legacy_bridge.py` is deleted or reduced to a dead-empty shim with no runtime usage
* [ ] No active runtime code imports `questionsapp.create_app()`
* [ ] No active runtime code imports `flask`
* [ ] FastAPI remains the single HTTP runtime path

**Checks:**

* `rg "LegacyServiceAdapter|FileCompat|create_app\\(|from flask|current_app|questionsapp\\." app questionsapp`
* `uvicorn app.main:app --host 127.0.0.1 --port 8000`

---

### Task 10

**Title:** `[Cleanup] Move active ORM models out of questionsapp namespace`

**Context:**
FastAPI runtime and DB session lifecycle are already native, but active app modules still depend on `questionsapp.models`, which blocks deletion of the legacy package and keeps old namespace coupling alive.

**Scope:**

* `questionsapp/models.py`
* `app/db/models.py` or `app/models/`
* all active imports in `app/repositories/*`, `app/services/*`, `app/workers/*`

**Implementation steps:**

1. Create native models module under `app/db/`.
2. Move ORM model definitions from `questionsapp.models` without changing table mapping or field names.
3. Replace imports in active runtime modules from `questionsapp.models` to the new module.
4. Keep legacy package untouched unless imports are fully migrated.
5. Do not change API contracts or DB schema behavior.

**Definition of Done:**

* [ ] active runtime no longer imports `questionsapp.models`
* [ ] `app/*` and `app/workers/*` use native model module
* [ ] no HTTP contract changes
* [ ] no task/worker behavior changes

**Checks:**

* `rg "questionsapp.models" app app/workers`
* `uvicorn app.main:app --host 127.0.0.1 --port 8000`

---

### Task 11

**Title:** `[Cleanup] Replace legacy question write handlers with native services`

**Checks:**

* `rg "app/services/legacy/questions" app`
* `rg "legacy_app|legacy_db" app`

---