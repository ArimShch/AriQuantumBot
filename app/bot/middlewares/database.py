import logging
from typing import Any, Callable, Awaitable

from aiogram import BaseMiddleware
from aiogram.types import Update

from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession


logger = logging.getLogger(__name__)

class DBSessionMiddleware(BaseMiddleware):
    async def __call__(
            self, 
            handler: Callable[[Update, dict[str, Any]], Awaitable[Any]], 
            event: Update, 
            data: dict[str, Any] 
    ) -> Any:
        session_factory: async_sessionmaker[AsyncSession] = data.get('session_factory')

        if session_factory is None:
            logger.error("Database pool is not provided in middleware data.")
            raise RuntimeError("Missing session_factory in middleware context.")
        
        async with session_factory() as session:
            try:
                async with session.begin():
                    data['session'] = session
                    result = await handler(event, data)
                return result
            except Exception as e:
                logger.exception("Transaction rolled back due to error: %s", str(e))
                raise


