# Khair Procurement Center

Проект реализует внутреннюю систему закупок для компании «Хайр Строй» с интеграцией Bitrix24, каталогом заводов и карточками заявок.

## Стек

- Backend: FastAPI + SQLAlchemy + PostgreSQL, Alembic
- Frontend: React + TypeScript + Vite + Ant Design
- Auth: JWT-based auth
- Demo mode: enabled by default for local development

## Быстрый старт

1. Создайте файл `.env` на основе `.env.example`.
2. Запустите docker-compose:

   docker compose up --build

3. Откройте frontend по адресу http://localhost:5173
4. Логин: `admin` / `admin123`

## Демонстрационный режим

Если не указаны параметры Bitrix24, приложение работает в демонстрационном режиме и подставляет тестовые данные.

## Backend API

Документация OpenAPI доступна по адресу:

http://localhost:8000/docs

## Тесты

Backend tests:

cd backend
pytest

Frontend build:

cd frontend
npm run build
