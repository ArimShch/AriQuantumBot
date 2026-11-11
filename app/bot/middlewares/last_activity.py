import logging
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

class LastActivityMiddleware(BaseMiddleware):
    async def __call__(
            self, 
            handler: Callable[[Update, dict[str, Any]], Awaitable[Any]], 
            event: Update, 
            data: dict[str, Any] 
    ) -> Any:
        user: User = data.get('event_from_user')

        if user is None:
            return await handler(event, data)
        
        session: AsyncSession = data.get('session')

        if session is None:
            logger.error('Database session not found in middleware data')
            raise RuntimeError('Missing database session for last_activity middleware')
        
        try:
            user_db = await user_repository.get_user(
                session=session, 
                tg_id=user.id
            )
            
            if not user_db:
                admin_ids = data.get('admin_ids')
                if user.id in admin_ids:
                    role_id = await base_repository.get_role_id(
                        session=session, 
                        name='admin'
                    )
                else:
                    role_id = await base_repository.get_role_id(
                        session=session, 
                        name='user'
                    )
                
                if user.language_code in ['ru', 'en']:
                    language_code = user.language_code
                else: 
                    language_code = 'en'

                user_db, user_setting_db = await base_repository.add_user_and_setting(
                    session=session, 
                    tg_id=user.id, 
                    username=user.username, 
                    first_name=user.first_name, 
                    last_name=user.last_name, 
                    role_id=role_id, 
                    language_code=language_code,
                    tg_locate=user.language_code, 
                )

                state: FSMContext = data["state"]
                await state.set_state(States.choose_language)
                data['is_new_user'] = True
            else: 
                current_time_utc = datetime.now(timezone.utc)
                
                # Проверяем, изменилась ли дата активности
                if user_db.last_activity.date() != current_time_utc.date():
                    # Обновляем все данные из Telegram
                    user_db.username = user.username
                    user_db.first_name = user.first_name
                    user_db.last_name = user.last_name
                    user_db.tg_locate = user.language_code
                    # Обновляем last_activity, чтобы не делать лишний запрос к БД
                    user_db.last_activity = datetime.now() 
                    
                    await session.flush()
                    logger.info("Updated user data on a new day for tg_id=%d", user.id)
                # Если день тот же, но прошло 5 минут - обновляем только активность
                elif current_time_utc - user_db.last_activity > timedelta(minutes=5):
                    await user_repository.update_user_last_activity(
                        session=session, 
                        tg_id=user.id
                    )
                data['is_new_user'] = False

            user_activity_today = await activity_repository.get_activity_today(
                session=session, tg_id=user.id 
            )

            if not user_activity_today:
                await activity_repository.create_activity_today(
                    session=session, 
                    tg_id=user.id, 
                )

        except Exception as e:
            await session.rollback()
            logger.error("Error in LastActivity middleware: %s", str(e))
            raise

        return await handler(event, data)