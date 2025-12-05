import asyncpg
import os
from typing import Optional


# Глобальный пул соединений к БД
pool: Optional[asyncpg.Pool] = None


async def create_pool() -> asyncpg.Pool:
    """Создание пула подключений к PostgreSQL."""
    global pool
    pool = await asyncpg.create_pool(
        host=os.getenv("DB_HOST", "localhost"),
        port=int(os.getenv("DB_PORT", 5432)),
        database=os.getenv("DB_NAME", "shop_bot"),
        user=os.getenv("DB_USER", "bot_user"),
        password=os.getenv("DB_PASS", "bot_password"),
        min_size=2,
        max_size=10,
    )
    return pool


async def close_pool():
    """Закрытие пула при остановке бота."""
    global pool
    if pool:
        await pool.close()
        pool = None


async def init_tables():
    """Инициализация таблиц в базе данных.
    Вызывается один раз при старте бота.
    """
    async with pool.acquire() as conn:
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS categories (
                id SERIAL PRIMARY KEY,
                name VARCHAR(128) NOT NULL,
                description TEXT DEFAULT ''
            );
        """)
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS products (
                id SERIAL PRIMARY KEY,
                category_id INTEGER REFERENCES categories(id) ON DELETE CASCADE,
                name VARCHAR(256) NOT NULL,
                description TEXT DEFAULT '',
                price NUMERIC(10, 2) NOT NULL,
                image_url TEXT DEFAULT '',
                in_stock BOOLEAN DEFAULT TRUE
            );
        """)
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                tg_id BIGINT UNIQUE NOT NULL,
                username VARCHAR(128) DEFAULT '',
                created_at TIMESTAMP DEFAULT NOW()
            );
        """)
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS cart_items (
                id SERIAL PRIMARY KEY,
                user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                product_id INTEGER REFERENCES products(id) ON DELETE CASCADE,
                quantity INTEGER DEFAULT 1,
                UNIQUE(user_id, product_id)
            );
        """)
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS orders (
                id SERIAL PRIMARY KEY,
                user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                address TEXT NOT NULL,
                total NUMERIC(10, 2) NOT NULL,
                status VARCHAR(32) DEFAULT 'created',
                created_at TIMESTAMP DEFAULT NOW()
            );
        """)


# --- Вспомогательные запросы для пользователей ---

async def get_or_create_user(tg_id: int, username: str = "") -> dict:
    """Получить пользователя по tg_id или создать нового."""
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT * FROM users WHERE tg_id = $1", tg_id
        )
        if row:
            return dict(row)
        row = await conn.fetchrow(
            "INSERT INTO users (tg_id, username) VALUES ($1, $2) RETURNING *",
            tg_id, username,
        )
        return dict(row)


# --- Каталог ---

async def get_categories() -> list[dict]:
    async with pool.acquire() as conn:
        rows = await conn.fetch("SELECT * FROM categories ORDER BY id")
        return [dict(r) for r in rows]


async def get_products_by_category(category_id: int) -> list[dict]:
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            "SELECT * FROM products WHERE category_id = $1 AND in_stock = TRUE ORDER BY id",
            category_id,
        )
        return [dict(r) for r in rows]


async def get_product(product_id: int) -> Optional[dict]:
    async with pool.acquire() as conn:
        row = await conn.fetchrow("SELECT * FROM products WHERE id = $1", product_id)
        return dict(row) if row else None


# --- Корзина ---

async def add_to_cart(user_id: int, product_id: int, qty: int = 1):
    """Добавить товар в корзину (или увеличить кол-во)."""
    async with pool.acquire() as conn:
        await conn.execute("""
            INSERT INTO cart_items (user_id, product_id, quantity)
            VALUES ($1, $2, $3)
            ON CONFLICT (user_id, product_id)
            DO UPDATE SET quantity = cart_items.quantity + $3
        """, user_id, product_id, qty)


async def get_cart(user_id: int) -> list[dict]:
    """Получить содержимое корзины с информацией о товарах."""
    async with pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT ci.id AS cart_item_id, ci.quantity, p.id AS product_id,
                   p.name, p.price
            FROM cart_items ci
            JOIN products p ON p.id = ci.product_id
            WHERE ci.user_id = $1
            ORDER BY ci.id
        """, user_id)
        return [dict(r) for r in rows]


async def update_cart_quantity(cart_item_id: int, delta: int):
    """Изменить количество товара в корзине. Удалить если <= 0."""
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT quantity FROM cart_items WHERE id = $1", cart_item_id
        )
        if not row:
            return
        new_qty = row["quantity"] + delta
        if new_qty <= 0:
            await conn.execute("DELETE FROM cart_items WHERE id = $1", cart_item_id)
        else:
            await conn.execute(
                "UPDATE cart_items SET quantity = $1 WHERE id = $2",
                new_qty, cart_item_id,
            )


async def clear_cart(user_id: int):
    """Очистить корзину пользователя после оформления заказа."""
    async with pool.acquire() as conn:
        await conn.execute("DELETE FROM cart_items WHERE user_id = $1", user_id)


# --- Заказы ---

async def create_order(user_id: int, address: str, total: float) -> dict:
    """Создать новый заказ."""
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "INSERT INTO orders (user_id, address, total, status) "
            "VALUES ($1, $2, $3, 'paid') RETURNING *",
            user_id, address, round(total, 2),
        )
        return dict(row)


async def get_orders(limit: int = 20) -> list[dict]:
    """Получить последние заказы (для админки)."""
    async with pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT o.*, u.tg_id, u.username
            FROM orders o
            JOIN users u ON u.id = o.user_id
            ORDER BY o.created_at DESC
            LIMIT $1
        """, limit)
        return [dict(r) for r in rows]


async def get_stats() -> dict:
    """Статистика: количество заказов, выручка."""
    async with pool.acquire() as conn:
        row = await conn.fetchrow("""
            SELECT COUNT(*) AS total_orders,
                   COALESCE(SUM(total), 0) AS revenue
            FROM orders
        """)
        return dict(row)
