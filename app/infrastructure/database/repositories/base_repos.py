import logging

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from ..models.models import User, Role, UserSetting, Language, ComplexityLevel, Backend

logger = logging.getLogger(__name__)

class BaseRepository:
    async def add_user_and_setting(
            self, 
            session: AsyncSession, 
            tg_id: int,
            username: str, 
            first_name: str, 
            last_name: str, 
            tg_locate: str, 
            role_id: int = 1,                       # user  
            language_code: str = 'en', 
    ) -> User:
        logger.info('Starting transaction "add_user" for user tg_id=%d', tg_id)

        user = User(
            id=tg_id, 
            username=username, 
            first_name=first_name, 
            last_name=last_name, 
            role_id=role_id,
            tg_locate=tg_locate, 
        )
        session.add(user)
        logger.info('User added. id=%d, username=%s, first_name=%s, last_name=%s', 
                    tg_id, username, first_name, last_name)

        user_settings = UserSetting(
            user_id=tg_id, 
            language_code=language_code
        )
        session.add(user_settings)
        logger.info('UserSetting added. user_id=%d, language_code=%s', 
                    tg_id, language_code)
        
        await session.flush()
        await session.refresh(user)
        
        logger.info('Transaction "add_user" completed successfully for user tg_id=%d', tg_id)

        # print(3, user, user_settings)
        # После создания user_settings
        # print("DEBUG: user =", user)
        # print("DEBUG: user_settings =", user_settings)
        # print("DEBUG: language_code =", user_settings.language_code)
        # print("DEBUG: complexity_level_id =", user_settings.complexity_level_id)
        # print("DEBUG: complexity_level object =", user_settings.complexity_level)
        # print("DEBUG: user.setting =", user.setting)
        return user, user_settings
    
    async def get_role_id(
            self, 
            session: AsyncSession, 
            name: str, 
    ) -> int:
        query = (
            select(Role)
            .where(Role.name == name) 
        )
        result = await session.execute(
            query
        )
        row = result.scalar_one_or_none()

        if row is None:
            raise ValueError(f"Role with name '{name}' not found in database")

        role_id = row.id

        logger.info('Get role id. id=%d', role_id)
        return role_id  
    
    # Функция, получающая все языки из БД
    async def get_languages(
            self, 
            session: AsyncSession, 
    ):
        query = (
            select(Language)
        )
        result = await session.execute(query)
        rows = result.scalars().all()

        logger.info('Get all languages')
        return rows 

    # Функция, получающая все уровни сложности из БД
    async def get_complexity_level(
            self, 
            session: AsyncSession, 
    ):
        query = (
            select(ComplexityLevel)
        )
        result = await session.execute(query)
        rows = result.scalars().all()

        logger.info('Get all Complexity Levels')
        return rows 
    
    # Функция, получающая все бэкенды из БД
    async def get_backends(
            self, 
            session: AsyncSession, 
    ):
        query = (
            select(Backend)
        )
        result = await session.execute(query)
        rows = result.scalars().all()

        logger.info('Get all Backends')
        return rows 

    async def get_all_users(
            self, 
            session: AsyncSession, 
    ):
        query = select(User.id)
        result = await session.execute(query)
        rows = result.scalars().all()

        logging.info('Get all Users')
        return rows

    async def get_all_users_with_settings(self, session: AsyncSession):
        query = select(User).options(selectinload(User.setting))
        result = await session.execute(query)
        return result.scalars().all()

