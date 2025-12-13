import time
from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Update

from app.database import get_or_create_user


class UserMiddleware(BaseMiddleware):
    """Мидлварь для работы с пользователями.
    Гарантирует что пользователь существует в БД и пробрасывает
    его данные в хендлеры через data['db_user'].
    """

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        # Извлекаем объект пользователя из разных типов апдейтов
        user = data.get("event_from_user")
        if user is not None:
            db_user = await get_or_create_user(
                tg_id=user.id,
                username=user.username or "",
            )
            data["db_user"] = db_user
        return await handler(event, data)


class ThrottlingMiddleware(BaseMiddleware):
    """Простой троттлинг по user_id.
    Ограничивает частоту запросов — не более одного за `rate_limit` секунд.
    """

    def __init__(self, rate_limit: float = 0.5):
        self.rate_limit = rate_limit
        self._cache: Dict[int, float] = {}
        super().__init__()

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        user = data.get("event_from_user")
        if user is not None:
            now = time.monotonic()
            last_time = self._cache.get(user.id, 0)
            if now - last_time < self.rate_limit:
                # Слишком частые запросы — просто игнорируем
                return
            self._cache[user.id] = now
        return await handler(event, data)
