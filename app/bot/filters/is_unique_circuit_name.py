from aiogram.filters import BaseFilter
from aiogram.types import Message

from sqlalchemy.ext.asyncio import AsyncSession
import logging

from ...infrastructure.database.repositories import circuit_repository


logger = logging.getLogger(__name__)


class IsUniqueCircuitName(BaseFilter):
    async def __call__(
            self, 
            message: Message, 
            session: AsyncSession, 
    ):
        try:
            circuit_name = message.text
            
            is_unique = await circuit_repository.is_unique_circuit_name(
                session=session, 
                tg_id=message.from_user.id, 
                name=circuit_name, 
            )

        except Exception as e:
            logger.error('Error in filter IsUniqueCircuitName: %s', e)
            is_unique = False

        print(is_unique)
        return is_unique 


        
            