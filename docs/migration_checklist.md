# FastAPI migration checklist (step 6)

Цель этого чеклиста — фиксировать готовность каждого endpoint к эксплуатации в FastAPI без изменения API-контрактов.

## 1. Контракт и маршрутизация

- [x] Префикс API сохранён: `/eduportal/questions`.
- [x] `GET /test/` перенесён и возвращает `Test success!!!`.
- [x] `GET /questions_api/` перенесён с прежней пагинацией и ответом.
- [x] `POST /questionslist/` перенесён.
- [x] `POST /spaceandroles/` перенесён.
- [x] `POST /saveorupdate/` перенесён с multipart + файлами.
- [x] `POST /service/` перенесён.
- [x] `POST /statistic/` перенесён.
- [x] `POST /botexcel/` перенесён.

## 2. Совместимость форматов

- [x] Legacy error-envelope сохранён: `{"status":"error","error_mess":"..."}`.
- [x] Legacy success-envelope сохранён для action-based endpoint’ов.
- [x] `questions_api` выдаёт legacy-формат с полями `count/page_count/page/data`.
- [x] Pydantic-схемы работают в permissive-режиме (`extra="allow"`) для обратной совместимости.

## 3. Валидация и обработка ошибок

- [x] Входные payload описаны в `app/schemas/payloads.py`.
- [x] `RequestValidationError` маппится в legacy-совместимую ошибку.
- [x] Централизованная обработка исключений зарегистрирована в `app/core/exceptions.py`.

## 4. Данные и lifecycle

- [x] Реализован lifecycle dependency для legacy SQLAlchemy session.
- [x] Rollback/remove выполняются централизованно в dependency.
- [x] Временная интеграция с legacy сервисами изолирована в `app/services/legacy_bridge.py`.

## 5. Операционная готовность

- [x] OpenAPI-спека актуализирована: `docs/openapi.json`.
- [x] Docker Compose переключён на ASGI запуск (`uvicorn app.main:app`).
- [x] В документации зафиксирован cutover и отсутствие breaking changes.
