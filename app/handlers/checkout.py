import os

from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from app import database as db
from app.states import CheckoutStates
from app.keyboards import confirm_order_kb, back_to_menu_kb

router = Router()


@router.callback_query(F.data == "checkout")
async def cb_checkout_start(callback: CallbackQuery, db_user: dict, state: FSMContext):
    """Начало оформления заказа — запрос адреса доставки."""
    items = await db.get_cart(db_user["id"])
    if not items:
        await callback.answer("Корзина пуста!", show_alert=True)
        return

    # Сохраняем корзину в FSM для последующего использования
    total = sum(float(i["price"]) * i["quantity"] for i in items)
    await state.update_data(cart_items=items, total=total)
    await state.set_state(CheckoutStates.waiting_address)

    await callback.message.edit_text(
        "📬 <b>Оформление заказа</b>\n\n"
        "Введите адрес доставки (город, улица, дом, квартира):",
        parse_mode="HTML",
    )
    await callback.answer()


@router.message(CheckoutStates.waiting_address)
async def process_address(message: Message, db_user: dict, state: FSMContext):
    """Получение адреса и переход к подтверждению оплаты."""
    address = message.text.strip()
    if len(address) < 5:
        await message.answer("Пожалуйста, укажите полный адрес (минимум 5 символов).")
        return

    await state.update_data(address=address)
    data = await state.get_data()

    # Формируем сводку заказа
    lines = ["📝 <b>Сводка заказа:</b>\n"]
    for item in data["cart_items"]:
        subtotal = float(item["price"]) * item["quantity"]
        lines.append(f"• {item['name']} x{item['quantity']} — {subtotal:.0f}₽")
    lines.append(f"\n📬 Адрес: {address}")
    lines.append(f"💰 <b>Итого: {data['total']:.0f} ₽</b>")
    lines.append("\nПодтвердите оплату:")

    await state.set_state(CheckoutStates.waiting_payment)
    await message.answer(
        "\n".join(lines),
        reply_markup=confirm_order_kb(),
        parse_mode="HTML",
    )


@router.callback_query(CheckoutStates.waiting_payment, F.data == "pay_confirm")
async def process_payment(
    callback: CallbackQuery, db_user: dict, state: FSMContext, bot: Bot
):
    """Mock-оплата: всегда успешна. Создаём заказ и уведомляем админа."""
    data = await state.get_data()
    address = data["address"]
    total = data["total"]

    # Создание заказа в БД
    order = await db.create_order(db_user["id"], address, total)
    await db.clear_cart(db_user["id"])
    await state.clear()

    await callback.message.edit_text(
        f"✅ <b>Заказ #{order['id']} оформлен!</b>\n\n"
        f"💳 Оплата прошла успешно (mock)\n"
        f"📬 Адрес: {address}\n"
        f"💰 Сумма: {total:.0f} ₽\n\n"
        "Спасибо за покупку! Мы свяжемся с вами для уточнения деталей.",
        reply_markup=back_to_menu_kb(),
        parse_mode="HTML",
    )
    await callback.answer("Оплата прошла успешно!", show_alert=True)

    # Уведомление администратора о новом заказе
    admin_id = os.getenv("ADMIN_ID")
    if admin_id:
        admin_text = (
            f"🔔 <b>Новый заказ #{order['id']}</b>\n\n"
            f"Пользователь: @{db_user.get('username', '—')} (tg_id: {db_user['tg_id']})\n"
            f"Адрес: {address}\n"
            f"Сумма: {total:.0f} ₽\n"
            f"Статус: {order['status']}"
        )
        try:
            await bot.send_message(int(admin_id), admin_text, parse_mode="HTML")
        except Exception:
            pass  # админ мог не начать чат с ботом


@router.callback_query(CheckoutStates.waiting_payment, F.data == "pay_cancel")
async def process_payment_cancel(callback: CallbackQuery, state: FSMContext):
    """Отмена оформления заказа."""
    await state.clear()
    await callback.message.edit_text(
        "❌ Оформление заказа отменено.\nКорзина сохранена.",
        reply_markup=back_to_menu_kb(),
    )
    await callback.answer()
