import logging
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, func
from sqlalchemy.orm import selectinload
    
from ..models.models import User, Role, UserSetting, QuantumCircuit, QuantumSimulation

logger = logging.getLogger(__name__)

class UserRepository:
    # Функция, получающая пользователя по его Телеграмм-ID
    async def get_user(
            self, 
            session: AsyncSession, 
            tg_id: int, 
    ) -> User | None:
        query = (
            select(User)
            .where(User.id == tg_id)
            # .options(
            #     selectinload(User.setting),
            #     selectinload(User.role),
            # )
        )
        result = await session.execute(
            query
        )
        row = result.scalar_one_or_none()

        logger.info('Row user is %s', row)
        return row 
    
    # Функция, обновляющая ref_source для пользователя
    async def update_user_ref_source(
            self, 
            session: AsyncSession, 
            tg_id: int, 
            ref_source: str, 
    ):
        query = (
            update(User)
            .where(User.id == tg_id)
            .values(ref_source=ref_source)
        )
        result = await session.execute(query)
        logger.info('Update user ref_source')
    
    # Функция, обновляющая последнюю активность пользователя
    async def update_user_last_activity(
            self, 
            session: AsyncSession, 
            tg_id: int, 
    ) -> None:
        query = (
            update(User)
            .where(User.id == tg_id)
            .values(last_activity=datetime.now())
        )
        result = await session.execute(query)

        logger.info('Updated user last_activity. tg_id=%d, last_activity=%s', 
                    tg_id, datetime.now())
        
    # Функция, получающая параметр qubit_input_text и automatic_name из настроек пользователя
    async def get_user_settings(
            self, 
            session: AsyncSession, 
            tg_id: int,
    ) -> UserSetting:
        query = (
            select(UserSetting)
            .where(UserSetting.user_id == tg_id)
        )
        result = await session.execute(
            query
        )
        row = result.scalar_one_or_none()

        logger.info('Row user-settings is %s', row)
        return row
    
    async def has_reached_circuit_limit(
            self, 
            session: AsyncSession, 
            tg_id: int, 
            limit: int = 5, 
    ) -> bool:
        query = (
            select(func.count(QuantumCircuit.id))
            .where(QuantumCircuit.user_id == tg_id)
        )
        result = await session.execute(
            query
        )
        row = result.scalar_one_or_none()
        
        logger.info('User have %s quantum circuits', row)
        row = limit if row is None else row 
        return row >= limit # возвращает true если кол-во схем пользователя равно limit или больше него
    
    # Функиця, возвращающая все объекты квантовых схем пользователя
    async def get_user_circuits(
            self,
            session: AsyncSession, 
            tg_id: int, 
    ):
        query = (
            select(QuantumCircuit)
            .where(QuantumCircuit.user_id == tg_id)
        )
        result = await session.execute(
            query
        )
        row = result.scalars().all()

        logger.info('User have circuits: %s', row)
        return row or []

    # Подсчёт количества схем пользователя
    async def get_user_circuits_count(self, session: AsyncSession, tg_id: int) -> int:
        query = select(func.count(QuantumCircuit.id)).where(QuantumCircuit.user_id == tg_id)
        result = await session.execute(query)
        
        return result.scalar_one() or 0

    # Подсчёт количества симуляций пользователя
    async def get_user_simulations_count(self, session: AsyncSession, tg_id: int) -> int:
        query = (
            select(func.count(QuantumSimulation.id))
            .where(QuantumSimulation.user_id == tg_id)
        )
        result = await session.execute(query)
        
        return result.scalar_one() or 0
    
    # Возврат заблокирован пользователь или нет
    async def get_is_blocked_user(self, session: AsyncSession, tg_id: int) -> bool:
        query = (
            select(User.is_blocked)
            .where(User.id == tg_id)
        )
        result = await session.execute(query)
        row = result.scalar_one_or_none()

        return row
    
    async def block_user_by_id(self, session: AsyncSession, user_id: int) -> bool:
        """Блокирует пользователя по ID. Возвращает True, если успешно."""
        stmt = (
            update(User)
            .where(User.id == user_id)
            .values(is_blocked=True)
        )
        result = await session.execute(stmt)
        return result.rowcount > 0


    async def block_user_by_username(self, session: AsyncSession, username: str) -> bool:
        """Блокирует пользователя по username (без @). Возвращает True, если успешно."""
        stmt = (
            update(User)
            .where(User.username == username)
            .values(is_blocked=True)
        )
        result = await session.execute(stmt)
        return result.rowcount > 0


    async def get_user_by_username(self, session: AsyncSession, username: str):
        """Получает пользователя по username (для проверки существования)."""
        stmt = select(User).where(User.username == username)
        result = await session.execute(stmt)
        return result.scalar_one_or_none()



        