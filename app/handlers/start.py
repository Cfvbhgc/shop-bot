from aiogram import Router, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, CallbackQuery

from app.keyboards import main_menu_kb

router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message, db_user: dict):
    """Обработчик команды /start — приветствие и главное меню."""
    text = (
        f"Привет, {message.from_user.first_name}! 👋\n\n"
        "Добро пожаловать в наш магазин.\n"
        "Выбирайте товары из каталога, добавляйте в корзину "
        "и оформляйте заказ прямо здесь.\n\n"
        "Используйте меню ниже для навигации:"
    )
    await message.answer(text, reply_markup=main_menu_kb())


@router.message(Command("help"))
async def cmd_help(message: Message, db_user: dict):
    """Справка по командам бота."""
    text = (
        "📋 <b>Доступные команды:</b>\n\n"
        "/start — главное меню\n"
        "/catalog — каталог товаров\n"
        "/cart — ваша корзина\n"
        "/help — эта справка\n\n"
        "Выбирайте категорию, нажимайте на товар "
        "и добавляйте его в корзину. Когда будете готовы — "
        "оформите заказ через корзину."
    )
    await message.answer(text, parse_mode="HTML")


@router.callback_query(F.data == "main_menu")
async def cb_main_menu(callback: CallbackQuery, db_user: dict):
    """Возврат в главное меню по нажатию inline-кнопки."""
    await callback.message.edit_text(
        "🏠 Главное меню\nВыберите действие:",
        reply_markup=main_menu_kb(),
    )
    await callback.answer()


@router.callback_query(F.data == "help")
async def cb_help(callback: CallbackQuery, db_user: dict):
    """Справка через inline-кнопку."""
    text = (
        "📋 <b>Доступные команды:</b>\n\n"
        "/start — главное меню\n"
        "/catalog — каталог товаров\n"
        "/cart — ваша корзина\n"
        "/help — эта справка"
    )
    await callback.message.edit_text(text, parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data == "noop")
async def cb_noop(callback: CallbackQuery):
    """Заглушка для информационных кнопок."""
    await callback.answer()
