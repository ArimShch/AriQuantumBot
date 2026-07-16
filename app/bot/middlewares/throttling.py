import logging
import time 
from collections import defaultdict
from typing import Any, Callable, Awaitable
from datetime import datetime, timedelta, timezone

from aiogram import BaseMiddleware
from aiogram.types import Update, User  
from aiogram.fsm.context import FSMContext

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from ...infrastructure.database.repositories import user_repository, base_repository, activity_repository
from ...infrastructure.database.models import models
from ..states.states import States


logger = logging.getLogger(__name__)

class ThrottlingMiddleware(BaseMiddleware):
    def __init__(self, limit_per_chat=3, period=1.0): 
        self.limit_per_chat = limit_per_chat  # 3 запроса в секунду на чат
        self.period = period
        self.storage = defaultdict(list)

    async def __call__(
            self, 
            handler: Callable[[Update, dict[str, Any]], Awaitable[Any]], 
            event: Update, 
            data: dict[str, Any] 
    ) -> Any:
        user: User = data.get('event_from_user')
        user_id = user.id 
        now = time.time()
        # Очищаем старые запросы
        self.storage[user_id] = [t for t in self.storage[user_id] 
                                 if now - t < self.period]
        
        if len(self.storage[user_id]) >= self.limit_per_chat:
            logger.warning(f'❌ Update was cancelled for @{user.username}.')
            return  # Игнорируем запрос
        
        self.storage[user_id].append(now)
        return await handler(event, data)

        



