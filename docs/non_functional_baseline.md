# Non-functional baseline (Step 1.2)

Цель: зафиксировать минимальные операционные метрики до переключения трафика на FastAPI,
чтобы сравнить деградации/улучшения после миграции.

## 1. SLI/SLO, которые нужно снять до миграции

- **Latency (p50/p95/p99)** по endpoint’ам:
  - `GET /questions_api/`
  - `POST /questionslist/`
  - `POST /service/`
  - `POST /saveorupdate/` (отдельно для multipart без файлов/с файлами)
- **Error rate**: доля 4xx/5xx по каждому endpoint.
- **Throughput**: RPS/requests per minute по endpoint и в целом.
- **Background side effects**:
  - время постановки Celery-задачи;
  - количество задач в очередях и доля ошибок задач.

## 2. Логирование и трассировка

До миграции собрать:

- Примеры production-логов c ключевыми полями:
  - timestamp,
  - method/path,
  - status,
  - duration,
  - correlation/request id (если есть),
  - exception stacktrace (для 5xx).
- Трассы/спаны (если есть APM) по критическим endpoint’ам.

После миграции ожидаемый минимум parity:

- единый JSON-формат логов;
- request id в заголовке `X-Request-ID`;
- latency логируется для каждого запроса.

## 3. План сравнения Flask vs FastAPI

1. Прогнать одинаковый набор запросов на Flask и FastAPI.
2. Сравнить:
   - коды ответов,
   - форматы ошибок,
   - payload shape,
   - latency/error rate.
3. Зафиксировать расхождения в отдельной таблице regression report.

## 4. Минимальный регрессионный чеклист

- Нет роста 5xx по ключевым endpoint’ам.
- p95 latency не хуже baseline на >10%.
- Форматы JSON-ответов совпадают с `docs/flask_api_snapshot.md`.
- Side effects (`botexcel`, `updtspacesbyconfl`) выполняются как и раньше.
