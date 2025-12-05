import asyncio
import logging
import os

from dotenv import load_dotenv
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from app.database import create_pool, close_pool, init_tables
from app.seed import seed_data
from app.middleware import UserMiddleware, ThrottlingMiddleware

# Подключаем роутеры хендлеров
from app.handlers import start, catalog, cart, checkout, admin

# Загрузка переменных окружения
load_dotenv()

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


async def on_startup(bot: Bot):
    """Действия при запуске бота: подключение к БД, миграции, сиды."""
    logger.info("Инициализация пула подключений к БД...")
    await create_pool()
    await init_tables()
    await seed_data()
    logger.info("База данных готова, бот запускается.")


async def on_shutdown(bot: Bot):
    """Корректное завершение: закрытие пула соединений."""
    logger.info("Остановка бота, закрытие соединений с БД...")
    await close_pool()


async def main():
    bot = Bot(
        token=os.getenv("BOT_TOKEN"),
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher()

    # Регистрация middleware — ключевая часть архитектуры.
    # Порядок имеет значение: сначала троттлинг, потом пользователь.
    dp.update.middleware(ThrottlingMiddleware(rate_limit=0.4))
    dp.update.middleware(UserMiddleware())

    # Подключение роутеров с хендлерами
    dp.include_router(start.router)
    dp.include_router(catalog.router)
    dp.include_router(cart.router)
    dp.include_router(checkout.router)
    dp.include_router(admin.router)

    # Хуки жизненного цикла
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)

    # Запуск поллинга
    logger.info("Бот запущен в режиме long-polling")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
