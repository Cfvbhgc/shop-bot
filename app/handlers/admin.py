import os

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from app import database as db
from app.keyboards import back_to_menu_kb

router = Router()


def _is_admin(tg_id: int) -> bool:
    """Проверка является ли пользователь администратором."""
    admin_id = os.getenv("ADMIN_ID", "0")
    return str(tg_id) == admin_id


@router.message(Command("orders"))
async def cmd_orders(message: Message, db_user: dict):
    """Список последних заказов (только для администратора)."""
    if not _is_admin(message.from_user.id):
        await message.answer("⛔ Эта команда доступна только администратору.")
        return

    orders = await db.get_orders(limit=15)
    if not orders:
        await message.answer("Заказов пока нет.", reply_markup=back_to_menu_kb())
        return

    lines = ["📋 <b>Последние заказы:</b>\n"]
    for o in orders:
        username = o.get("username") or "—"
        lines.append(
            f"#{o['id']} | @{username} | {float(o['total']):.0f}₽ | "
            f"{o['status']} | {o['created_at'].strftime('%d.%m %H:%M')}"
        )
    await message.answer("\n".join(lines), parse_mode="HTML")


@router.message(Command("stats"))
async def cmd_stats(message: Message, db_user: dict):
    """Статистика магазина (только для администратора)."""
    if not _is_admin(message.from_user.id):
        await message.answer("⛔ Эта команда доступна только администратору.")
        return

    stats = await db.get_stats()
    total_orders = stats["total_orders"]
    revenue = float(stats["revenue"])

    text = (
        "📊 <b>Статистика магазина</b>\n\n"
        f"Всего заказов: {total_orders}\n"
        f"Общая выручка: {revenue:.0f} ₽"
    )
    await message.answer(text, parse_mode="HTML")
