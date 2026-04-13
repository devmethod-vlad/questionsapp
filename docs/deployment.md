# Deployment notes (Docker Compose + uv)

## Что изменено

- Базовый Python-образ обновлен до `python:3.11-slim-bookworm`.
- Для установки зависимостей используется `uv sync` из `pyproject.toml` (без ручного `freeze`).
- В `docker-compose.yml` добавлены проверки обязательных volume-переменных через `${VAR:?err}`.
- Добавлен healthcheck для `questionsapp`.
- Сборка разделена на `dev`, `prod` и `cron`: код копируется только в `prod`/`cron`, а `dev` рассчитан на bind-mount исходников.

## Практики работы с переменными окружения

1. Не храните секреты в репозитории. Используйте только `.env.example` как шаблон.
2. Создайте локальный `.env` и заполните секреты значениями из вашего секрет-хранилища.
3. Для CI/CD прокидывайте секреты через инструменты платформы (GitHub Secrets, Vault и т.д.).
4. Критичные переменные (`POSTGRES_USER`, `POSTGRES_PASSWORD`, `PG_CONTAINER`, `PG_BASE`, `QUESTIONS_ATTACHMENTS`) должны быть заполнены всегда — приложение теперь валидирует это при старте.
5. Если пароль БД содержит спецсимволы, они безопасно кодируются при формировании `SQLALCHEMY_DATABASE_URI`.

## Управление зависимостями (uv + pyproject.toml)

- Добавить пакет: `uv add <package>`
- Удалить пакет: `uv remove <package>`
- Установить/синхронизировать окружение: `uv sync`
- Запускать команды в окружении проекта: `uv run <command>`

## Рекомендуемые следующие шаги

- Добавить `pydantic-settings` для централизованной схемы env-переменных перед миграцией на FastAPI.
- Разделить env-файлы по окружениям (`.env.dev`, `.env.stage`, `.env.prod`) и использовать отдельные compose override-файлы.
- Подключить проверку `.env` в prestart-скрипте (например, `python -m questionsapp.env_check`).

## FastAPI запуск (ASGI)

После миграции API-слоя на FastAPI можно запускать отдельный ASGI процесс:

- Dev: `uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000`
- Prod: `uv run gunicorn -k uvicorn.workers.UvicornWorker app.main:app -b 0.0.0.0:8000`

Старый Flask WSGI вход (`wsgi.py`) можно оставить временно для поэтапного cutover.
