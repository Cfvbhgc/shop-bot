from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


# --- Главное меню ---

def main_menu_kb() -> InlineKeyboardMarkup:
    """Клавиатура главного меню."""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="📦 Каталог", callback_data="catalog"),
        InlineKeyboardButton(text="🛒 Корзина", callback_data="cart"),
    )
    builder.row(
        InlineKeyboardButton(text="ℹ️ Помощь", callback_data="help"),
    )
    return builder.as_markup()


# --- Каталог ---

def categories_kb(categories: list[dict]) -> InlineKeyboardMarkup:
    """Клавиатура с категориями товаров."""
    builder = InlineKeyboardBuilder()
    for cat in categories:
        builder.row(
            InlineKeyboardButton(
                text=cat["name"],
                callback_data=f"cat_{cat['id']}",
            )
        )
    builder.row(
        InlineKeyboardButton(text="◀️ Назад", callback_data="main_menu")
    )
    return builder.as_markup()


def products_kb(products: list[dict], category_id: int) -> InlineKeyboardMarkup:
    """Список товаров в выбранной категории."""
    builder = InlineKeyboardBuilder()
    for prod in products:
        price_str = f"{prod['price']:.0f}₽"
        builder.row(
            InlineKeyboardButton(
                text=f"{prod['name']} — {price_str}",
                callback_data=f"prod_{prod['id']}",
            )
        )
    builder.row(
        InlineKeyboardButton(text="◀️ К категориям", callback_data="catalog")
    )
    return builder.as_markup()


def product_card_kb(product_id: int, category_id: int) -> InlineKeyboardMarkup:
    """Карточка товара: добавить в корзину + навигация."""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="🛒 В корзину",
            callback_data=f"add_{product_id}",
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="◀️ Назад к товарам",
            callback_data=f"cat_{category_id}",
        )
    )
    return builder.as_markup()


# --- Корзина ---

def cart_kb(cart_items: list[dict]) -> InlineKeyboardMarkup:
    """Корзина: кнопки +/- для каждого товара, оформить, очистить."""
    builder = InlineKeyboardBuilder()
    for item in cart_items:
        # Название и количество
        builder.row(
            InlineKeyboardButton(
                text=f"➖",
                callback_data=f"cartminus_{item['cart_item_id']}",
            ),
            InlineKeyboardButton(
                text=f"{item['name']} x{item['quantity']}",
                callback_data="noop",
            ),
            InlineKeyboardButton(
                text=f"➕",
                callback_data=f"cartplus_{item['cart_item_id']}",
            ),
        )
    if cart_items:
        builder.row(
            InlineKeyboardButton(text="✅ Оформить заказ", callback_data="checkout")
        )
        builder.row(
            InlineKeyboardButton(text="🗑 Очистить корзину", callback_data="clear_cart")
        )
    builder.row(
        InlineKeyboardButton(text="◀️ Меню", callback_data="main_menu")
    )
    return builder.as_markup()


# --- Оформление заказа ---

def confirm_order_kb() -> InlineKeyboardMarkup:
    """Подтверждение заказа перед оплатой."""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="💳 Оплатить", callback_data="pay_confirm"),
        InlineKeyboardButton(text="❌ Отмена", callback_data="pay_cancel"),
    )
    return builder.as_markup()


def back_to_menu_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="◀️ В меню", callback_data="main_menu")
    )
    return builder.as_markup()
