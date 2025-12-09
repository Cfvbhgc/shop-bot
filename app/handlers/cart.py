from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery

from app import database as db
from app.keyboards import cart_kb, back_to_menu_kb

router = Router()


async def _render_cart(db_user: dict) -> tuple[str, any]:
    """Сформировать текст корзины и клавиатуру.
    Возвращает кортеж (text, reply_markup).
    """
    items = await db.get_cart(db_user["id"])
    if not items:
        return "🛒 Ваша корзина пуста.", back_to_menu_kb()

    lines = ["🛒 <b>Ваша корзина:</b>\n"]
    total = 0
    for item in items:
        subtotal = float(item["price"]) * item["quantity"]
        total += subtotal
        lines.append(
            f"• {item['name']} — {item['quantity']} шт. × "
            f"{float(item['price']):.0f}₽ = {subtotal:.0f}₽"
        )
    lines.append(f"\n<b>Итого: {total:.0f} ₽</b>")
    text = "\n".join(lines)
    return text, cart_kb(items)


@router.message(Command("cart"))
async def cmd_cart(message: Message, db_user: dict):
    """Показать содержимое корзины по команде."""
    text, kb = await _render_cart(db_user)
    await message.answer(text, reply_markup=kb, parse_mode="HTML")


@router.callback_query(F.data == "cart")
async def cb_cart(callback: CallbackQuery, db_user: dict):
    """Показать корзину через inline-кнопку."""
    text, kb = await _render_cart(db_user)
    await callback.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data.startswith("cartplus_"))
async def cb_cart_plus(callback: CallbackQuery, db_user: dict):
    """Увеличить количество товара на 1."""
    cart_item_id = int(callback.data.split("_")[1])
    await db.update_cart_quantity(cart_item_id, delta=1)
    text, kb = await _render_cart(db_user)
    await callback.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data.startswith("cartminus_"))
async def cb_cart_minus(callback: CallbackQuery, db_user: dict):
    """Уменьшить количество товара на 1 (удалить если 0)."""
    cart_item_id = int(callback.data.split("_")[1])
    await db.update_cart_quantity(cart_item_id, delta=-1)
    text, kb = await _render_cart(db_user)
    await callback.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data == "clear_cart")
async def cb_clear_cart(callback: CallbackQuery, db_user: dict):
    """Полная очистка корзины."""
    await db.clear_cart(db_user["id"])
    await callback.message.edit_text(
        "🗑 Корзина очищена.",
        reply_markup=back_to_menu_kb(),
    )
    await callback.answer()
