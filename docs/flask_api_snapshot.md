# Flask API Snapshot (Step 1.1)

> Цель: зафиксировать текущее поведение API для безопасной миграции на FastAPI без breaking changes.
>
> Источники: статический анализ `questionsapp/routes.py` и связанных сервисов.

## 1) Глобальные правила

- Базовый префикс всех маршрутов: `app.config['URL_PREFIX']` (по умолчанию `/eduportal/questions`).
- Глобальный CORS включен для всего приложения (`CORS(app)`).
- JSON отдается в UTF-8 (`ensure_ascii=False`, `application/json; charset=utf-8`).
- Глобальной обязательной авторизации на уровне middleware/декораторов нет.
- Rate limit явно включен только для одного endpoint: `GET /questions_api/` (60 req/min на IP).

## 2) API endpoints (бизнес-API)

Ниже только backend API (без страниц/статики).

---

### 2.1 `GET {URL_PREFIX}/test/`

**Назначение:** тестовый health-like endpoint.

- Query params: нет.
- Headers: не требуются.
- Body: нет.

**Успех**
- `200 text/plain`: `Test success!!!`

**Ошибки**
- Явно не заданы.

---

### 2.2 `GET {URL_PREFIX}/questions_api/`

**Назначение:** публичная выдача вопросов/ответов с пагинацией.

- Query params:
  - `publicorder` (string, optional, default `"0"`; `"1"` => только публичные)
  - `page_count` (string->int, optional, default `100`, min clamp `1`, max clamp `500`)
  - `page` (string->int, optional, default `1`, min clamp `1`)
- Headers: не требуются.
- Body: нет.

**Успех**
- `200 application/json`
```json
{
  "count": 123,
  "page_count": 100,
  "page": 1,
  "data": ["..."]
}
```

**Ошибки**
- `400`
```json
{
  "status": "error",
  "error_mess": "Invalid pagination parameters; must be integers."
}
```
- `500`
```json
{
  "status": "error",
  "error_mess": "Internal server error while fetching data."
}
```

**Особенности**
- Декоратор `@limiter.limit("60 per minute")`.
- Форма каждого элемента `data` определяется `get_questions_api_data(...)`.

---

### 2.3 `POST {URL_PREFIX}/questionslist/`

**Назначение:** формирование списка вопросов или поиск вопроса в списке.

- Content-Type: `application/json`.
- Body поля:
  - `userid`, `roleid`, `orderid`, `spaceid`, `statusid`, `perpagecount`, `activepage`,
    `datesort`, `searchinput`, `enablesearch`, `isfeedback`, `showonlypublic`,
    `usertoken`, `forsynchroflag`, `findquestioninlist`.
- Headers: не требуются (авторизация встроена в payload через `usertoken`).

**Успех/ошибки**
- Возвращаемый JSON делегирован в:
  - `find_question_in_list(params)` если `findquestioninlist` truthy,
  - иначе `form_questions_list(params)`.
- При неверном методе (теоретически):
```json
{"status": "error", "error_mess": "WARN: Incorrect request method"}
```

**Особенности**
- Внутри `form_questions_list` есть проверка токена (`check_user_token`).

---

### 2.4 `POST {URL_PREFIX}/spaceandroles/`

**Назначение:** действия со space/roles.

- Content-Type: `application/json`.
- Body поля:
  - `action` (required)
  - `spaceid`, `roleid`, `userid`

**Успех**
- При `action == "getrolesbyspace"`: делегируется в `get_roles_by_space(spaceid, roleid, userid)`.

**Ошибки**
- Нет `action`:
```json
{"status": "error", "error_mess": "WARN: No action param"}
```
- Неизвестный `action`:
```json
{"status": "error", "error_mess": "WARN: No valid action param"}
```
- Неверный метод (теоретически):
```json
{"status": "error", "error_mess": "WARN: Incorrect request method"}
```

---

### 2.5 `POST {URL_PREFIX}/saveorupdate/`

**Назначение:** создание/обновление вопроса + multipart вложения.

- Content-Type: `multipart/form-data`.
- Form fields:
  - `action` (required)
  - `spacekey`, `orderid`, `userid`, `unionroleid`, `question_text`, `answer_text`,
    `publicorder`, `fastformflag`, `userfingerprintid`, `fio`, `login`, `muname`,
    `phone`, `mail`, `isfeedback`
- File fields:
  - `question_files[]` (list)
  - `answer_files[]` (list)
- Headers: не требуются.

**Успех**
- `action == "save_question"` -> `save_question(params)`
- `action == "save_combine"` -> `save_combine(params)`
- `action == "save_anonym_question"` -> `save_anonym_question(params)`

**Ошибки**
- Нет `action` / невалидный `action` / неверный метод:
  - `{"status":"error","error_mess":"WARN: No action param"}`
  - `{"status":"error","error_mess":"WARN: No valid action param"}`
  - `{"status":"error","error_mess":"WARN: Incorrect request method"}`

**Особенности**
- Ключевой endpoint для миграции: смешанные текстовые поля + файлы.

---

### 2.6 `POST {URL_PREFIX}/service/`

**Назначение:** мульти-операционный service endpoint.

- Content-Type: `application/json`.
- Body поля:
  - Базовые: `action`, `orderid`, `userid`, `attachid`, `execute_action`, `publicflag`,
    `attach_target`, `edulogin`, `adminlogin`, `adminpass`
  - Для config: `tokenlifetime`, `botname`, `uploadsize`

**Action mapping**
- `execaction` -> `exec_action(execute_action, orderid, userid)`
- `changefilepublicity` -> `change_attach_publicity(attachid, publicflag)`
- `deleteattachment` -> `delete_attachment(attach_target, attachid, orderid, userid)`
- `createnewadmin` -> `create_new_admin(edulogin, adminlogin, adminpass)`
- `changeadminpass` -> `change_admin_pass(userid, adminpass)`
- `updateappconfig` -> `update_app_config(app_params)`
- `getappconfiginfo` -> `get_appconfig_info()`
- `enteradmin` -> `enter_admin(adminlogin, adminpass, userid)`
- `exitadmin` -> `exit_admin(userid)`
- `updtspacesbyconfl` -> `update_spaces_info.delay()` + `{"status":"ok"}`

**Ошибки**
- Нет `action` / невалидный `action` / неверный метод:
  - `{"status":"error","error_mess":"WARN: No action param"}`
  - `{"status":"error","error_mess":"WARN: No valid action param"}`
  - `{"status":"error","error_mess":"WARN: Incorrect request method"}`

**Особенности**
- Здесь фактически API-комбайн. На миграции лучше сохранить URL/форматы, но внутри разбить на отдельные handlers.

---

### 2.7 `POST {URL_PREFIX}/statistic/`

**Назначение:** статистика бота.

- Content-Type: `application/json`.
- Body поля:
  - `action`
  - `botstatskind` (`newusers` | `phrazestats` | `phrazesperday`)
  - `botimeperiod` (`7` или `30`)
  - `botdownloadflag`

**Успех**
- При `action == "getbotstat"` и валидных параметрах:
  - `newusers` -> `get_newuser_stat(delta, botdownloadflag)`
  - `phrazestats` -> `get_phraze_stat(delta, botdownloadflag)`
  - `phrazesperday` -> `get_perdayphrazes_stat(delta, botdownloadflag)`

**Ошибки**
- Нет обязательных параметров:
```json
{"status": "error", "error_mess": "WARN: No params"}
```
- Нет/невалидный `action`/неверный метод:
```json
{"status": "error", "error_mess": "WARN: No action param"}
```
```json
{"status": "error", "error_mess": "WARN: No valid action param"}
```
```json
{"status": "error", "error_mess": "WARN: Incorrect request method"}
```

---

### 2.8 `POST {URL_PREFIX}/botexcel/`

**Назначение:** запуск задач формирования excel/выгрузок + уведомление в Telegram.

- Content-Type: `application/json`.
- Body поля:
  - `action` (`getfollowersexcel` | `getsuppinfo`)
  - `chatid`

**Успех**
- При валидных `action + chatid`: `{"status":"ok"}`
- Триггер side effects:
  - Telegram сообщение через `_tg_post(...)`
  - Celery task (`delay`) в production, иначе синхронный вызов функции.

**Ошибки**
- Нет параметров:
```json
{"status": "error", "error_mess": "WARN: No params"}
```
- Невалидный action:
```json
{"status": "error", "error_mess": "WARN: No valid action param"}
```
- Неверный метод:
```json
{"status": "error", "error_mess": "WARN: Incorrect request method"}
```

## 3) Небизнесовые HTTP-маршруты (важно для parity)

### 3.1 Static serving
- Набор GET маршрутов `.../static/...` с `send_from_directory(..., as_attachment=True)`.
- Включая динамические path params для вложений:
  - `/static/attachments/orders/<int:userid>/<int:orderid>/<path:filename>`
  - `/static/attachments/answers/<int:userid>/<int:orderid>/<path:filename>`

### 3.2 HTML templates
- `GET /main/` -> `questions.html`
- `GET /webappauth/` -> `webappauth.html`
- `GET /webappanonymviewer/` -> `webappanonymviewer.html`
- `GET /webapp/` -> `webapp.html`

> Если эти страницы остаются в FastAPI, нужно отдельно учесть Jinja2Templates и current behavior query-проверок.

## 4) Форматы ответов и контрактные риски

### 4.1 Что уже явно видно
- Во многих ошибках используется envelope:
```json
{"status": "error", "error_mess": "..."}
```
- Успешный ответ часто `{"status": "ok"}` для action endpoints.
- Для `questions_api` — отдельный пагинационный формат без `status`.

### 4.2 Что нужно дополнительно зафиксировать runtime-тестами
- Точные поля JSON из сервисов (`form_questions_list`, `exec_action`, `enter_admin`, и т.д.)
- Типы nullable-полей и их фактическая сериализация.
- Поведение на невалидном `Content-Type`.
- Порядок ключей JSON (если внешние клиенты действительно от него зависят).

## 5) Особые кейсы сериализации/типов

- JSON в UTF-8 (`ensure_ascii=False`) — важно сохранить в FastAPI JSONResponse настройками.
- Multipart c массивами файлов (`question_files[]`, `answer_files[]`).
- Celery side effects в `/service` и `/botexcel`.
- В route-слое явной сериализации `Decimal/Enum/datetime` нет; потенциально происходит в сервисах/ORM моделях и требует отдельной инвентаризации ответов через контрактные тесты.

## 6) Авторизация/аутентификация и middleware-поведение

- Нет глобального auth middleware.
- Токен-проверка реализуется выборочно в сервисном слое (например, `form_questions_list` -> `check_user_token`).
- Входные токены передаются в JSON (`usertoken`) либо через action endpoint (`enteradmin`, `exitadmin` и т.п.).
- CORS включен глобально для всех маршрутов.
- Rate limit только на `GET /questions_api/`.