import logging
from typing import Any, Callable, Awaitable
from fluentogram import TranslatorHub, TranslatorRunner
from sqlalchemy.ext.asyncio import AsyncSession

from aiogram import BaseMiddleware
from aiogram.types import Update, User

from ...infrastructure.database.models import models
from ...infrastructure.database.repositories import user_repository


logger = logging.getLogger(__name__)

class I18nMiddleware(BaseMiddleware):
    def __init__(self, hub: TranslatorHub):
        self.hub = hub 

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
            raise RuntimeError('Missing database session for i18n middleware')
        
        # print('Middleware i18n')
        # print('EventCallbackQuery', event.callback_query)
        # print('User choice language:', event.callback_query.data.split(':')[-1])
        # print('Callback-data:', event.callback_query.data)

        user_db: models.User = await user_repository.get_user(
            session=session, 
            tg_id=user.id,
        )
        data['user_db'] = user_db 

        if user_db is None:
            logger.error('User model not found in middleware data')
            raise RuntimeError('The User model record is missing for i18n middleware')
        
        try:
            if event.callback_query: 
                if event.callback_query.data.startswith('settings:language:') or event.callback_query.data.startswith('lang:'):
                    user_lang_code = event.callback_query.data.split(':')[-1]
                else:
                    user_lang_code = user_db.setting.language_code
            else:
                user_lang_code = user_db.setting.language_code

            user_complexity_level = user_db.setting.complexity_level.name
            # print(user_lang_code, user_complexity_level)

            i18n = self.hub.get_translator_by_locale(
                locale=user_lang_code
            )

            data['i18n'] = i18n
            data['locale'] = user_db.setting.language_code 
            data['user_complexity_level'] = user_complexity_level
        except Exception as e:
            await session.rollback()
            logger.error("Error in I18n middleware: %s", str(e))

        return await handler(event, data)



