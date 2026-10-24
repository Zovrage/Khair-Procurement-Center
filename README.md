# Khair Procurement Center

Внутренняя система отдела закупок компании «Хайр Строй»: вход по ролям, центр заявок, справочник заводов, фиксация отправки и номеров заказов. Демо-данные помечаются как демонстрационные и не считаются данными CRM.

## Стек

- Backend: FastAPI + SQLAlchemy + PostgreSQL, Alembic
- Frontend: React + TypeScript + Vite + Ant Design
- Auth: JWT-based auth
- Demo mode: enabled by default for local development

## Быстрый старт

1. Скопируйте `.env.example` в `.env` и задайте уникальные `SECRET_KEY` и пароль PostgreSQL (обновите `POSTGRES_PASSWORD` и `DATABASE_URL` согласованно).
2. Для демо оставьте `DEMO_MODE=true`. Для production установите `APP_ENV=production`, `DEMO_MODE=false`, задайте `INITIAL_ADMIN_USERNAME` и сильный `INITIAL_ADMIN_PASSWORD` (12-72 UTF-8 байта), затем удалите пароль bootstrap из `.env` после первого успешного старта.
3. Запустите Docker Compose:

   docker compose up --build

4. Откройте frontend по адресу `http://localhost:5173` или `http://<IP-сервера>:5173`.
5. Демо-учётные записи: `admin / admin123`, `buyer / buyer123`, `manager / manager123`.

## Демонстрационный режим

Демо-режим включён для локального старта. Приложение при старте создаёт тестовые записи только в выбранной базе. Для production используйте отдельную чистую базу и задайте `DEMO_MODE=false`.
При первом production-запуске начальный администратор создаётся из переменных `INITIAL_ADMIN_*`, если в базе нет пользователей. В production включены secure HttpOnly cookie и CSRF-проверка; сайт следует размещать за HTTPS.

## Подключение Bitrix24

После настройки интеграции выполняется периодическая сверка Bitrix24 (по умолчанию каждые 300 секунд); администратор также может запустить ручную синхронизацию. На сервере задайте:

- `BITRIX_PORTAL_URL` — адрес портала, например `https://company.bitrix24.ru`.
- `BITRIX_WEBHOOK_URL` — полный URL входящего вебхука с правами на чтение сделок. Это секрет; не размещайте его во frontend и не добавляйте в git.
- `BITRIX_DEAL_PIPELINE_ID` — ID воронки сделок из CRM.
- `TIMEZONE` — часовой пояс отображения, по умолчанию `Europe/Moscow`.
- `BITRIX_SYNC_INTERVAL_SECONDS` — период автоматической сверки, минимум 60 секунд.

После изменения `.env` перезапустите backend. Система не подставляет ID воронки автоматически. Сделки синхронизируются идемпотентно; сделки, которых больше нет в настроенной воронке, переводятся в историю без удаления данных закупки.

Миграции Alembic выполняются при запуске backend-контейнера.

## Backend API

Документация OpenAPI доступна по адресу:

http://localhost:8000/docs

## Тесты

Backend tests:

cd backend
python -m pytest app/tests -q

Frontend build:

cd frontend
npm run build
