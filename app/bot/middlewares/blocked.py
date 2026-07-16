from aiogram import BaseMiddleware
from aiogram.types import Update

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

import logging

from ...infrastructure.database.models.models import User
from ...infrastructure.database.repositories import user_repository

logger = logging.getLogger(__name__)

class BlockMiddleware(BaseMiddleware):
    async def __call__(self, handler, event: Update, data: dict):
        user: User = data.get('event_from_user')

        if user is None:
            return await handler(event, data)
        
        session: AsyncSession = data.get('session')

        if session is None:
            logger.error('Database session not found in middleware data')
            raise RuntimeError('Missing database session for BlockMiddleware middleware')

        # Проверяем, заблокирован ли пользователь
        is_blocked = await user_repository.get_is_blocked_user(session, user.id)

        if is_blocked:
            # НЕ пропускаем обработку дальше
            return

        return await handler(event, data)