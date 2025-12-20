# Shop Bot — Telegram-магазин

Телеграм-бот для онлайн-магазина с каталогом товаров, корзиной, оформлением заказа и уведомлениями администратора.

## Стек

- Python 3.11
- aiogram 3.x (middleware-архитектура)
- PostgreSQL 15 (asyncpg)
- Docker + Docker Compose

## Возможности

- Каталог с категориями и карточками товаров
- Корзина с кнопками +/- и подсчётом итога
- Оформление заказа через FSM (адрес → оплата → подтверждение)
- Mock-оплата (всегда успешна)
- Уведомление администратора о новых заказах
- Админ-команды: `/orders`, `/stats`
- Throttling и автоматическая регистрация пользователей через middleware

## Быстрый старт

```bash
# Скопировать конфигурацию
cp .env.example .env
# Заполнить BOT_TOKEN и ADMIN_ID в .env

# Запуск через Docker
docker compose up --build
```

## Команды бота

| Команда    | Описание                         |
|------------|----------------------------------|
| `/start`   | Главное меню                     |
| `/catalog` | Каталог товаров                  |
| `/cart`    | Корзина                          |
| `/help`    | Справка                          |
| `/orders`  | Последние заказы (только админ)  |
| `/stats`   | Статистика магазина (только админ)|

## Структура проекта

```
shop-bot/
├── app/
│   ├── bot.py           # Точка входа, инициализация
│   ├── middleware.py     # UserMiddleware, ThrottlingMiddleware
│   ├── database.py      # Пул asyncpg, таблицы, запросы
│   ├── seed.py          # Начальные данные
│   ├── keyboards.py     # Inline-клавиатуры
│   ├── states.py        # FSM-состояния
│   └── handlers/
│       ├── start.py     # /start, /help
│       ├── catalog.py   # Каталог и карточки товаров
│       ├── cart.py      # Корзина
│       ├── checkout.py  # Оформление заказа (FSM)
│       └── admin.py     # Админ-команды
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
└── .env.example
```
