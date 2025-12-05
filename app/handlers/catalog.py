from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery

from app import database as db
from app.keyboards import categories_kb, products_kb, product_card_kb, back_to_menu_kb

router = Router()


@router.message(Command("catalog"))
async def cmd_catalog(message: Message, db_user: dict):
    """Показать список категорий при вводе команды /catalog."""
    categories = await db.get_categories()
    if not categories:
        await message.answer("Каталог пока пуст. Загляните позже!")
        return
    await message.answer(
        "📦 <b>Каталог товаров</b>\nВыберите категорию:",
        reply_markup=categories_kb(categories),
        parse_mode="HTML",
    )


@router.callback_query(F.data == "catalog")
async def cb_catalog(callback: CallbackQuery, db_user: dict):
    """Показать категории по нажатию inline-кнопки."""
    categories = await db.get_categories()
    if not categories:
        await callback.message.edit_text("Каталог пока пуст.")
        await callback.answer()
        return
    await callback.message.edit_text(
        "📦 <b>Каталог товаров</b>\nВыберите категорию:",
        reply_markup=categories_kb(categories),
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(F.data.startswith("cat_"))
async def cb_category_products(callback: CallbackQuery, db_user: dict):
    """Отображение товаров выбранной категории."""
    category_id = int(callback.data.split("_")[1])
    products = await db.get_products_by_category(category_id)
    if not products:
        await callback.answer("В этой категории пока нет товаров", show_alert=True)
        return
    # Получаем название категории из первого товара не идеально,
    # но для простоты — подтягиваем из списка категорий
    categories = await db.get_categories()
    cat_name = next(
        (c["name"] for c in categories if c["id"] == category_id),
        "Категория",
    )
    text = f"📂 <b>{cat_name}</b>\nВыберите товар:"
    await callback.message.edit_text(
        text,
        reply_markup=products_kb(products, category_id),
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(F.data.startswith("prod_"))
async def cb_product_card(callback: CallbackQuery, db_user: dict):
    """Карточка товара с описанием и кнопкой добавления в корзину."""
    product_id = int(callback.data.split("_")[1])
    product = await db.get_product(product_id)
    if not product:
        await callback.answer("Товар не найден", show_alert=True)
        return
    price_str = f"{product['price']:.0f}"
    text = (
        f"🏷 <b>{product['name']}</b>\n\n"
        f"{product['description']}\n\n"
        f"💰 Цена: <b>{price_str} ₽</b>\n"
        f"{'✅ В наличии' if product['in_stock'] else '❌ Нет в наличии'}"
    )
    await callback.message.edit_text(
        text,
        reply_markup=product_card_kb(product_id, product["category_id"]),
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(F.data.startswith("add_"))
async def cb_add_to_cart(callback: CallbackQuery, db_user: dict):
    """Добавить товар в корзину пользователя."""
    product_id = int(callback.data.split("_")[1])
    product = await db.get_product(product_id)
    if not product:
        await callback.answer("Товар не найден", show_alert=True)
        return
    await db.add_to_cart(db_user["id"], product_id, qty=1)
    await callback.answer(
        f"✅ «{product['name']}» добавлен в корзину",
        show_alert=False,
    )
